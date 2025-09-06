"""
LangGraph ReAct Agent for LoyaltyAnalytics
Uses FastMCP tools for database queries and visualizations.
"""

import json
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
from decimal import Decimal

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool

from config import settings
from langraph_multi_mcp_tools import get_all_mcp_langraph_tools
from mcp_multi_client import mcp_manager as multi_mcp_manager
from mcp_ui_generator import mcp_ui_generator

logger = logging.getLogger(__name__)


def ensure_json_serializable(obj: Any) -> Any:
    """Recursively ensure all objects are JSON serializable."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: ensure_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    else:
        return obj


class AgentState(TypedDict):
    """State for the LangGraph ReAct agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    database_schema: Optional[str]
    sql_query: Optional[str]
    query_results: Optional[List[Dict[str, Any]]]
    visualization_config: Optional[Dict[str, Any]]
    reasoning: List[str]
    current_step: str
    is_conversational: bool
    iteration_count: int
    max_iterations: int
    tool_results: List[Dict[str, Any]]
    goal_achieved: bool


class LangGraphReActAgent:
    """
    Simplified ReAct agent implemented with LangGraph and FastMCP tools.
    Follows the Reasoning + Acting pattern for analytics queries.
    
    Architecture: reasoning ⟷ tool_calling → reasoning (final response) → END
    
    The reasoning node handles both:
    1. Initial analysis and tool selection
    2. Final response generation after tool execution
    
    This eliminates the need for a separate response_generation_node.
    """
    
    def __init__(self):
        self.llm = None
        self.tools: List[BaseTool] = []
        self.graph = None
        
        # Use a persistent MemorySaver to ensure conversations are remembered
        self.memory = MemorySaver()
        
        # Dictionary to store conversation histories by session ID
        self.session_histories = {}
        self._initialized = False
        

        # Use OpenAI for better tool calling support
        if settings.openai_api_key:
            self.llm = ChatOpenAI(
                openai_api_key=settings.openai_api_key,
                model="gpt-4-turbo-preview",
                temperature=0.1  
            )          
    
    async def initialize(self):
        """Initialize the LangGraph agent with Multi-MCP tools."""
        if self._initialized:
            return
        
        logger.info("Initializing LangGraph ReAct agent...")
        
        # Initialize multi-MCP manager
        await multi_mcp_manager.initialize()
        
        # Get all available tools from multiple MCP servers
        self.tools = await get_all_mcp_langraph_tools()
        logger.info(f"Loaded {len(self.tools)} tools for the agent: {[tool.name for tool in self.tools]}")
        
        # Create the LangGraph workflow
        self._create_graph()
        
        self._initialized = True
        logger.info("LangGraph ReAct agent initialized successfully")
    
    def _create_graph(self):
        """Create the LangGraph state graph for the ReAct pattern."""
        if not self.llm:
            logger.warning("No LLM available - agent will use fallback responses")
            return
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes - simplified architecture without response_generation_node
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("tool_calling", self._tool_calling_node)
        
        # Add edges with conditional routing for loop-back architecture
        workflow.add_conditional_edges(
            "reasoning",
            self._should_use_tools,
            {
                "tools": "tool_calling",
                "end": END  # Reasoning node handles final response, go directly to END
            }
        )
        
        # Tool calling goes back to reasoning for loop-back
        workflow.add_conditional_edges(
            "tool_calling",
            self._should_continue_reasoning,
            {
                "continue": "reasoning",
                "end": END  # When done with tools, reasoning will generate final response
            }
        )
        
        # Set entry point
        workflow.set_entry_point("reasoning")
        
        # Compile the graph with memory and recursion limit
        self.graph = workflow.compile(
            checkpointer=self.memory,
            interrupt_before=[],
            interrupt_after=[],
            debug=False
        )
        
        logger.info("LangGraph workflow created successfully with simplified architecture")
    
    def _should_use_tools(self, state: AgentState) -> str:
        """Determine if we should use tools based on the current state."""
        messages = state.get("messages", [])
        iteration_count = state.get("iteration_count", 0)
        tool_results = state.get("tool_results", [])
        goal_achieved = state.get("goal_achieved", False)
        
        logger.info(f"🔍 _should_use_tools CALLED - iteration={iteration_count}, messages={len(messages)}, tool_results={len(tool_results)}, goal_achieved={goal_achieved}")
        
        # If goal is already achieved, end the workflow
        if goal_achieved:
            logger.info(f"🔍 DECISION: Goal achieved -> END")
            return "end"
        
        # Check if the last message has tool calls that need to be executed
        if messages:
            last_message = messages[-1]
            logger.info(f"🔍 Last message type: {type(last_message).__name__}")
            logger.info(f"🔍 Last message content preview: {str(last_message.content)[:100]}...")
            
            if (hasattr(last_message, 'tool_calls') and 
                last_message.tool_calls and 
                len(last_message.tool_calls) > 0):
                logger.info(f"🔍 DECISION: Found {len(last_message.tool_calls)} tool calls to execute -> TOOLS")
                for i, tool_call in enumerate(last_message.tool_calls):
                    logger.info(f"🔍 Tool call {i}: {tool_call.get('name', 'unknown')} with args: {tool_call.get('args', {})}")
                return "tools"
        
        # If no tool calls, the reasoning node has provided the final response -> END
        logger.info(f"🔍 DECISION: No tool calls found, reasoning complete -> END")
        return "end"
    
    def _should_continue_reasoning(self, state: AgentState) -> str:
        """Determine if we should continue reasoning or end after tool execution."""
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 3)
        goal_achieved = state.get("goal_achieved", False)
        tool_results = state.get("tool_results", [])
        
        logger.info(f"🚦 _should_continue_reasoning CALLED - iteration={iteration_count}, max={max_iterations}, tool_results={len(tool_results)}, goal_achieved={goal_achieved}")
        
        # Safety check: prevent infinite loops
        if iteration_count >= max_iterations:
            logger.info(f"🚦 DECISION: Max iterations ({max_iterations}) reached -> END")
            return "end"
        
        # If goal is achieved, end the workflow
        if goal_achieved:
            logger.info("🚦 DECISION: Goal achieved -> END")
            return "end"
        
        # All queries now have full memory, no need for special handling
        # Continue with standard flow
        
        # Always continue to reasoning after tool execution to analyze results and generate response
        # The reasoning node will determine if more tools are needed or if it can provide final response
        logger.info(f"🚦 DECISION: Continue to reasoning for result analysis and response generation -> CONTINUE")
        return "continue"
    
    async def _tool_calling_node(self, state: AgentState) -> AgentState:
        """Custom tool calling node with better logging and state tracking."""
        iteration_count = state.get("iteration_count", 0)
        logger.info(f"🔧 TOOL CALLING NODE STARTED - iteration: {iteration_count}")
        try:
            
            # Use the standard ToolNode but with logging
            tool_node = ToolNode(self.tools)
            logger.info("🔧 Created ToolNode, executing tools")
            result_state = await tool_node.ainvoke(state)
            logger.info(f"🔧 ToolNode completed successfully, messages count: {len(result_state.get('messages', []))}")
            
            # 🔥 FIX: Preserve existing tool_results from input state, not result_state
            tool_results = state.get("tool_results", [])  # Get from input state!
            messages = result_state.get('messages', [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    logger.info(f"🔧 Tool result preview: {str(last_message.content)[:200]}...")
                    logger.info(f"🔧 Tool result type: {type(last_message)}")
                    
                    # Store tool result for analysis
                    tool_result_entry = {
                        "iteration": iteration_count,
                        "content": last_message.content,
                        "timestamp": datetime.now().isoformat(),
                        "success": not ("Error:" in str(last_message.content) and "TypeError" in str(last_message.content))
                    }
                    tool_results.append(tool_result_entry)
                    logger.info(f"🔧 Added tool result: success={tool_result_entry['success']}")
            
            # 🔥 FIX: Merge result_state with our preserved state
            result_state["tool_results"] = tool_results
            result_state["iteration_count"] = iteration_count
            result_state["goal_achieved"] = state.get("goal_achieved", False)  # Preserve goal status
            
            logger.info(f"🔧 TOOL CALLING NODE FINISHED - tool_results count: {len(tool_results)}, iteration: {iteration_count}")
            return result_state
        except Exception as e:
            logger.error(f"Error in tool calling node: {e}")
            # Add error message to state
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append(AIMessage(content=f"Tool execution failed: {str(e)}"))
            
            # Keep same iteration count on error
            state["iteration_count"] = state.get("iteration_count", 0)
            state["goal_achieved"] = True  # Stop on fatal errors
            return state
    
    async def _reasoning_node(self, state: AgentState) -> AgentState:
        """
        Reasoning node: Analyze user query and plan actions.
        Enhanced for loop-back architecture with continuation logic.
        """
        user_query = state["user_query"]
        reasoning = state.get("reasoning", [])
        iteration_count = state.get("iteration_count", 0)
        tool_results = state.get("tool_results", [])
        
        # Determine if this is a continuation after tool execution
        # If we have tool results, this is a continuation (we've executed tools before)
        is_continuation = len(tool_results) > 0
        
        # If this is a continuation, increment iteration count for next cycle
        if is_continuation:
            iteration_count += 1
            state["iteration_count"] = iteration_count
            
        # Check for special states that require specific handling
        current_step = state.get("current_step", "")
        if current_step == "code_execution_required":
            logger.info("🧠 CODE EXECUTION REQUIRED: Agent must execute code examples before providing them")
            # Force the agent to use code execution tools
            state["reasoning"].append("Code examples detected without execution - must run code in sandbox first")
            # Set a specific instruction for the LLM
            state["user_query"] = f"{user_query} [IMPORTANT: Execute ALL code examples in the sandbox before providing them to the user. Use execute_python_code or execute_code tools.]"
            # Reset the step
            state["current_step"] = "processing"
        
        # Check if this is a code-related query that requires execution
        code_related_keywords = ['code example', 'code snippet', 'python code', 'javascript code', 'show me code', 'demonstrate code']
        if any(keyword.lower() in user_query.lower() for keyword in code_related_keywords):
            logger.info("🧠 CODE-RELATED QUERY DETECTED: Must execute code before providing examples")
            # Force the agent to use code execution tools
            reasoning.append("Code-related query detected - must execute code in sandbox before providing examples")
            # Set a specific instruction for the LLM
            state["user_query"] = f"{user_query} [IMPORTANT: Execute ALL code examples in the sandbox before providing them to the user. Use execute_python_code or execute_code tools.]"
            # Ensure goal is not achieved until code is executed
            state["goal_achieved"] = False
        
        # 🔥 FIX: Check for repeated failures and stop infinite loops
        failed_attempts = 0
        consecutive_failures = 0
        
        # Safely check tool results to prevent 'list' object has no attribute 'get' error
        for result in tool_results:
            if isinstance(result, dict) and not result.get("success", True):
                failed_attempts += 1
        
        for result in reversed(tool_results):
            if isinstance(result, dict) and not result.get("success", True):
                consecutive_failures += 1
            else:
                break
        
        logger.info(f"🧠 REASONING: iteration={iteration_count}, tool_results={len(tool_results)}, is_continuation={is_continuation}, failed_attempts={failed_attempts}, consecutive_failures={consecutive_failures}")
        
        # Get current conversation messages for context (used throughout this method)
        current_messages = state.get("messages", [])
        logger.info(f"🔍 DEBUG: current_messages length: {len(current_messages)}, types: {[type(msg).__name__ for msg in current_messages]}")
        
        # Stop if we have too many consecutive failures (tool issues)
        if consecutive_failures >= 2:
            logger.warning(f"🧠 STOPPING: {consecutive_failures} consecutive tool failures detected")
            state["goal_achieved"] = True
            if self.llm:
                error_response = await self.llm.ainvoke([
                    SystemMessage(content="You are a helpful assistant that explains technical issues."),
                    HumanMessage(content=f"The user asked: '{user_query}'\n\nBut there were technical issues with the database tools. Please explain that there's a database connectivity or configuration issue and suggest they contact support.")
                ])
                state["messages"].append(error_response)
                state["reasoning"].append("Stopped due to repeated tool failures")
                return state
        
        # Check for conversational queries (only on first iteration)
        if iteration_count == 0:
            # Skip conversational responses for code-related queries - they need tool execution
            if any(keyword.lower() in user_query.lower() for keyword in ['code example', 'code snippet', 'python code', 'javascript code', 'show me code', 'demonstrate code']):
                logger.info("🧠 CODE-RELATED QUERY: Skipping conversational response, forcing tool execution")
                # Fall through to tool execution workflow
            else:
                # ALL queries always get full conversation history via our session memory system
                # No keyword detection - agent decides what to return based on the full conversation context
                if self.llm:
                    try:
                        # Generate a conversational response with conversation history if available
                        conversation_messages = [SystemMessage(content="You are a friendly and helpful analytics assistant. You have access to the full conversation history and can reference previous exchanges with the user.")]
                        
                        # Include ALL conversation context for better responses, especially for context references
                        if current_messages:
                            # Add ALL previous messages for complete context
                            conversation_messages.extend(current_messages)
                            logger.info(f"🧠 CONVERSATIONAL: Added {len(current_messages)} messages to context")
                        
                        # Only add the current query if not already included in current_messages
                        if not current_messages or current_messages[-1].content != user_query:
                            conversation_messages.append(HumanMessage(content=user_query))
                        
                        # Make sure tools are available for all queries
                        if self.tools:
                            llm_with_tools = self.llm.bind_tools(self.tools)
                            response = await llm_with_tools.ainvoke(conversation_messages)
                        else:
                            response = await self.llm.ainvoke(conversation_messages)
                        state["messages"].append(response)
                        reasoning.append("Processing query with full conversation history.")
                        state["current_step"] = "response_generation"
                        state["reasoning"] = reasoning
                        return state
                    except Exception as e:
                        logger.error(f"Conversational response error: {e}")
                        # Fall through to default logic
        
        system_prompt = self._get_system_prompt(iteration_count if is_continuation else 0, tool_results, current_messages)
        
        if self.llm:
            try:
                # Build context based on whether this is first iteration or continuation
                if not is_continuation:
                    # First iteration: Include ALL conversation history + current query
                    messages = [SystemMessage(content=system_prompt)]
                    
                    # Include ALL previous conversation messages for complete context
                    if current_messages:
                        # Use all available messages for proper conversation memory
                        logger.info(f"🔍 DEBUG: Using all {len(current_messages)} messages for context")
                        # Extend with all current messages to ensure full conversation history
                        messages.extend(current_messages)
                        logger.info(f"🧠 MEMORY: Added all {len(current_messages)} messages to LLM context")
                    else:
                        logger.info(f"🔍 DEBUG: No previous messages to add. current_messages length: {len(current_messages)}")
                    
                    # Check if we need to add the user query separately
                    if not (current_messages and isinstance(current_messages[-1], HumanMessage) and current_messages[-1].content == user_query):
                        messages.append(HumanMessage(content=user_query))
                    reasoning.append(f"Starting analysis of query: {user_query}")
                else:
                    # Continuation: Analyze what we have so far and decide next steps
                    continuation_prompt = self._build_continuation_prompt(user_query, tool_results)
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=continuation_prompt)
                    ]
                    reasoning.append(f"Iteration {iteration_count}: Analyzing tool results and generating final response")
                
                # For all non-conversational queries, bind tools to the LLM
                if self.tools:
                    llm_with_tools = self.llm.bind_tools(self.tools)
                    response = await llm_with_tools.ainvoke(messages)
                else:
                    # Fallback if no tools are available
                    response = await self.llm.ainvoke(messages)
                
                # Add the AI response to messages (including any tool calls)
                state["messages"].append(response)
                
                # 🔍 DETAILED LOGGING OF LLM RESPONSE
                logger.info(f"🧠 REASONING NODE OUTPUT:")
                logger.info(f"🧠 - Iteration: {iteration_count}")
                logger.info(f"🧠 - Is continuation: {is_continuation}")
                logger.info(f"🧠 - Conversation context: {len(current_messages)} messages in history")
                logger.info(f"🧠 - Response content: {response.content}")
                logger.info(f"🧠 - Has tool_calls: {hasattr(response, 'tool_calls')}")
                if hasattr(response, 'tool_calls'):
                    logger.info(f"🧠 - Tool calls count: {len(response.tool_calls) if response.tool_calls else 0}")
                    if response.tool_calls:
                        for i, tc in enumerate(response.tool_calls):
                            logger.info(f"🧠 - Tool call {i}: {tc}")
                
                # Extract reasoning if available
                if response.content:
                    if is_continuation:
                        reasoning.append(f"Iteration {iteration_count} Analysis: {response.content}")
                    else:
                        reasoning.append(f"Initial Analysis: {response.content}")
                
                state["reasoning"] = reasoning
                
                # Determine next step: if no tool calls, this IS the final response
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    next_step = "tool_execution"
                    logger.info(f"🧠 REASONING NODE DECISION: Next step = {next_step} (found {len(response.tool_calls)} tool calls)")
                else:
                    # No tool calls = this response IS the final answer
                    next_step = "completed" 
                    state["goal_achieved"] = True
                    logger.info(f"🧠 REASONING NODE DECISION: Task completed, final response generated: {response.content[:100]}...")
                
                state["current_step"] = next_step
                
            except Exception as e:
                logger.error(f"Reasoning node error: {e}")
                reasoning.append(f"Reasoning error: {str(e)}")
                # Add error message to state
                state["messages"].append(AIMessage(content=f"I encountered an error: {str(e)}"))
                state["reasoning"] = reasoning
                state["current_step"] = "error"
        else:
            # Fallback without LLM
            reasoning.append("No LLM available - using heuristic analysis")
            fallback_response = f"I understand you're asking: '{user_query}'. To provide detailed analytics, please configure a Google API key (GOOGLE_API_KEY) for enhanced AI processing with Gemini."
            state["messages"].append(AIMessage(content=fallback_response))
            state["reasoning"] = reasoning
            state["current_step"] = "schema_discovery"
        
        return state
    

    
    def _get_system_prompt(self, iteration_count: int = 0, tool_results: List[Dict[str, Any]] = None, messages: List[BaseMessage] = None) -> str:
        """Get the system prompt for the ReAct agent with iteration context and conversation history."""
        available_tools = [f"- {tool.name}: {tool.description}" for tool in self.tools]
        tools_list = "\n".join(available_tools)
        
        # 🔥 FIX: Add conversation context to system prompt
        conversation_context = ""
        if messages and len(messages) > 1:
            # Count previous exchanges (excluding current message)
            previous_exchanges = (len(messages) - 1) // 2  # Rough estimate of back-and-forth
            conversation_context = f"""
IMPORTANT - CONVERSATION MEMORY:
You DO have access to the full conversation history in this session. There are {len(messages)} total messages in this conversation.
When users ask "what did I ask earlier?" or "what was my previous question?", you CAN and SHOULD reference the conversation history.
You can see all previous user messages and your own responses. Use this context to provide helpful, contextual responses.

CONVERSATION CONTEXT:
You are continuing an ongoing conversation with {previous_exchanges} previous exchanges in this session.
Always consider the conversation history when responding to maintain context and provide relevant follow-up information.
If the user refers to something from earlier, reference the specific messages in the conversation history.
"""
        
        base_prompt = f"""You are an expert data analyst AI for LoyaltyAnalytics platform.

Your role is to help users analyze their e-commerce and redemption data using natural language queries.
{conversation_context}
Available Tools:
{tools_list}

Database Schema Context:
The database contains three main tables:
- **merchants**: Store information (id, merchant_name, category, created_at, status)
- **users**: Customer information (id, email, first_name, last_name, created_at, status)  
- **redemptions**: Transaction data (id, user_id, merchant_id, amount, points_used, redemption_date, status)

**IMPORTANT**: Use these exact table names in your SQL queries:
- ✅ Use: `redemptions` (not redemption_data)
- ✅ Use: `merchants` (not merchant_data)
- ✅ Use: `users` (not user_data)

Current date: {datetime.now().strftime('%Y-%m-%d')}
"""

        if iteration_count == 0:
            return base_prompt + """
Your Process:
1. UNDERSTAND: Analyze the user's question to understand what data they need
2. PLAN: Determine what SQL query will get the required data
3. EXECUTE: Use tools to get schema (if needed), execute queries, and create visualizations
4. RESPOND: Provide clear, helpful responses with appropriate visualizations

SPECIAL INSTRUCTIONS FOR CODE EXAMPLES:
- When user asks for code examples → EXECUTE the code first using sandbox tools
- When user asks for code explanations → EXECUTE the code first using sandbox tools
- When user asks for programming help → EXECUTE the code first using sandbox tools
- NEVER provide code blocks without execution

Guidelines:
- Always use safe, read-only SQL queries
- Choose appropriate visualization types for the data
- Provide clear explanations of your analysis
- If the query is ambiguous, ask for clarification
- For complex requests, break them down into steps (e.g., first get data, then create visualization)

CODE EXAMPLE RULES - ABSOLUTELY CRITICAL:
- **NEVER provide code examples without executing them first in the sandbox**
- **NEVER show ```python or ```javascript blocks without running the code first**
- **ALWAYS execute code through execute_python_code or execute_code tools before showing examples**
- **If user asks for code examples, execute them first, then show working code with results**
- **This ensures all code examples are tested and functional**
- **VIOLATION: If you see code blocks in your response, you MUST execute them first**

VISUALIZATION REQUIREMENTS:
- If user asks for chart, graph, histogram, visualization, or figure → You MUST create a visualization
- **CRITICAL: ALWAYS use these composite tools for visualizations:**
  - **create_chart_from_data**: Creates chart from database query + optional code processing
  - **create_table_from_data**: Creates table from database query + optional code processing  
  - **create_histogram_from_data**: Creates histogram from database query + optional code processing
- **FORBIDDEN: NEVER use these deprecated tools:**
  - ❌ create_chart (DEPRECATED - requires pre-fetched data)
  - ❌ create_table (DEPRECATED - requires pre-fetched data)  
  - ❌ create_histogram (DEPRECATED - requires pre-fetched data)
- ALWAYS query the database FIRST to get data, THEN create visualizations
- NEVER provide final response without creating requested visualizations
- These tools handle the complete workflow: Database Query → Code Processing → UIResource Generation
- No raw data is sent to the LLM - only the final UIResource
- Use these for all data visualization requests

WORKFLOW OPTIONS:
1) **RECOMMENDED: Composite Data Tools**: Use create_chart_from_data, create_table_from_data, create_histogram_from_data
   - Single tool call handles: Database Query → Code Processing → UIResource Generation
   - No raw data sent to LLM
   - Cleaner, more efficient workflow

PYTHON SANDBOX - CRITICAL RULES:
- execute_python_code: Execute Python code for data analysis, processing, or custom visualizations
- Use this when you need to process data, create custom calculations, or generate visualizations
- **NEVER provide code examples without executing them first in the sandbox**
- **ALWAYS run code through the sandbox before showing results to users**
- **If user asks for code examples, execute them first, then show working code with results**
- Example workflow: Execute code → Show results → Provide working code example
"""
        else:
            return base_prompt + f"""
CONTINUATION MODE - Iteration {iteration_count}:
You have already executed some tools. Review what has been accomplished so far and determine:

1. Is the user's original request fully satisfied?
2. Do you need additional tools to complete the task?
3. Should you create a visualization if data was retrieved?
4. Are you ready to provide a final response?

Previous tool executions: {len(tool_results) if tool_results else 0}

Decision Logic:
- If you have data but need visualization → Call visualization tool
- If you need more data or different analysis → Call appropriate database/analysis tools  
- If the task is complete → **IMPORTANT: Provide NO tool calls to proceed to final response**
- Always consider multi-step workflows (data retrieval → analysis → visualization)

CRITICAL: When you have sufficient data to answer the user's question, DO NOT call more tools. 
Simply provide your analysis without any tool calls to generate the final response.

VISUALIZATION LOGIC:
- If the user asks for a chart, graph, histogram, visualization, or figure → You MUST call a visualization tool
- **CRITICAL: ALWAYS use composite tools**: create_chart_from_data, create_table_from_data, create_histogram_from_data
- **NEVER use the basic create_chart, create_table, or create_histogram tools**
- Only provide final response AFTER creating the requested visualization

Guidelines for Tool Selection:
- **VISUALIZATION: ALWAYS use composite tools (create_chart_from_data, create_table_from_data, create_histogram_from_data)**
- **NEVER use basic visualization tools (create_chart, create_table, create_histogram)**
- Use file system tools for saving results or accessing configurations
- **Use Python sandbox tools to execute ANY code examples before providing them to users**
- **Stop calling tools once you have what you need to answer the question**

CODE EXECUTION REQUIREMENTS:
- **NEVER provide code examples without executing them first**
- **ALWAYS use execute_python_code tool for Python examples**
- **ALWAYS use execute_code tool for other language examples**
- **Show execution results, then provide working code**
"""
    
    def _build_continuation_prompt(self, original_query: str, tool_results: List[Dict[str, Any]]) -> str:
        """Build a prompt for continuation iterations based on previous tool results."""
        results_summary = []
        has_errors = False
        has_successful_data = False
        
        for i, result in enumerate(tool_results):
            content_preview = str(result.get("content", ""))[:500]  # Show more content for better analysis
            success = result.get("success", True)
            if not success:
                has_errors = True
                results_summary.append(f"Tool Result {i+1} (FAILED): {content_preview}")
            else:
                has_successful_data = True
                results_summary.append(f"Tool Result {i+1} (SUCCESS): {content_preview}")
        
        error_guidance = ""
        if has_errors and not has_successful_data:
            error_guidance = """
⚠️ CRITICAL: Previous tool calls have FAILED with errors. DO NOT retry the same tool calls.
Instead, provide a helpful response explaining what went wrong and suggest alternatives.
"""
        elif has_errors:
            error_guidance = """
⚠️ Some tool calls failed, but you have some successful data. Use the successful data to answer.
"""
        
        return f"""Original User Query: {original_query}

Tool Results from Previous Executions:
{chr(10).join(results_summary)}

{error_guidance}

INSTRUCTIONS:
Analyze the tool results above and determine:

1. **Check for Tool Errors:**
   - If tools are failing repeatedly, DO NOT retry them
   - Provide a helpful explanation and suggest alternatives

2. **Is the user's request satisfied?**
   - If YES: Generate a comprehensive, user-friendly response. DO NOT call any tools.
   - If NO and no errors: Call different/corrected tools to complete the task.

3. **For FINAL RESPONSES:**
   - Synthesize any successful results into a clear, helpful answer
   - If tools failed, explain the issue and provide guidance
   - Address the original query directly
   - Be conversational and informative

4. **VISUALIZATION CHECK:**
   - If user requested a chart, graph, histogram, or visualization → You MUST call a visualization tool
   - If you have data but no visualization was created → Call appropriate visualization tool
   - Only provide final response AFTER creating the requested visualization

CRITICAL: If previous tool calls failed, DO NOT call the same tools again. Instead, explain the issue or try alternative approaches.

VISUALIZATION TOOLS AVAILABLE:
- create_histogram: For histogram requests (distribution of values)
  - Requires: title, data (from database query), value_field (column name), bin_count (optional)
- create_chart: For bar, line, pie charts
  - Requires: title, chart_type, data (from database query), x_axis, y_axis
- create_table: For data table displays
  - Requires: title, data (from database query), columns (optional)

CRITICAL: When calling visualization tools, you MUST pass the actual data from your database query results.
Example: If you got data from database query, pass that exact data to the visualization tool.

DATA PASSING RULE: Always pass the exact data array from your database query to the visualization tool's 'data' parameter.

IMPORTANT: You must have data from a database query before calling visualization tools. If you don't have data yet, call database tools first."""
    
    async def process_query(self, user_query: str, session_id: str) -> Dict[str, Any]:
        """
        Process a user query through the LangGraph ReAct agent.
        
        Args:
            user_query: Natural language query from the user
            session_id: The session ID for the user
            
        Returns:
            Dict with response data including type, content, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create config for checkpointer
            config = {
                "configurable": {"thread_id": session_id},
                "recursion_limit": 10  # Set reasonable recursion limit
            }
            
            # DUAL MEMORY SYSTEM: Retrieve conversation history from both checkpoint and our backup
            previous_messages = []
            
            # 1. First check our backup session histories dictionary
            if session_id in self.session_histories:
                previous_messages = self.session_histories[session_id]
                logger.info(f"🧠 MEMORY: Retrieved {len(previous_messages)} previous messages from backup memory for session {session_id}")
            
            # 2. If no backup found, try the LangGraph checkpoint
            elif self.memory and self.graph:
                try:
                    # Get the last checkpoint for this session
                    checkpoint_tuple = await self.memory.aget_tuple(config)
                    if checkpoint_tuple and checkpoint_tuple.checkpoint:
                        # Extract previous messages from checkpoint
                        checkpoint_data = checkpoint_tuple.checkpoint
                        if "channel_values" in checkpoint_data and "messages" in checkpoint_data["channel_values"]:
                            previous_messages = checkpoint_data["channel_values"]["messages"] or []
                            logger.info(f"🧠 MEMORY: Retrieved {len(previous_messages)} previous messages from checkpoint for session {session_id}")
                            # Update our backup with what we found in the checkpoint
                            self.session_histories[session_id] = previous_messages
                        else:
                            logger.info(f"🧠 MEMORY: No previous messages found in checkpoint for session {session_id}")
                    else:
                        logger.info(f"🧠 MEMORY: No previous checkpoint found for session {session_id} - starting fresh conversation")
                except Exception as e:
                    logger.warning(f"🧠 MEMORY: Failed to retrieve conversation history: {e}")
                    # Continue with empty history rather than failing
            
            # Create a new human message for the current query
            current_message = HumanMessage(content=user_query)
            
            # Add the new message to our backup memory system
            if session_id not in self.session_histories:
                self.session_histories[session_id] = []
            self.session_histories[session_id].append(current_message)
            
            # Build input data with conversation context
            # Include all previous messages as initial state, plus current message
            input_data = {
                "messages": previous_messages + [current_message],
                "user_query": user_query,
                "iteration_count": 0,
                "tool_results": [],
                "goal_achieved": False
            }
            
            # Log conversation context for debugging
            total_messages = len(previous_messages) + 1  # +1 for current message
            logger.info(f"🧠 MEMORY: Processing query with {total_messages} total messages in conversation context")
            
            # Execute the graph if available
            if self.graph:
                # Run the graph with the full conversation history
                final_state = await self.graph.ainvoke(input_data, config)
                
                # Important: Update our backup memory with any new AI responses
                if "messages" in final_state:
                    all_messages = final_state["messages"]
                    # Only keep messages that aren't already in our backup
                    for msg in all_messages:
                        if msg not in self.session_histories[session_id]:
                            self.session_histories[session_id].append(msg)
                            logger.info(f"🧠 MEMORY: Added new message to backup memory for session {session_id}")
                
                # Extract results
                return self._format_response(final_state)
            else:
                # No LangGraph available
                return {
                    "type": "error",
                    "response": "LangGraph is not available. Please check the LLM configuration.",
                    "reasoning": ["No LLM or graph configured"]
                }
                
        except Exception as e:
            import traceback
            logger.error(f"Query processing error: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "type": "error",
                "response": f"I encountered an error processing your query: {str(e)}",
                "reasoning": [f"Error: {str(e)}"]
            }
    
    def _format_response(self, state: AgentState) -> Dict[str, Any]:
        """Format the final agent response from the simplified workflow."""
        # Get the actual AI response from the last message
        messages = state.get("messages", [])
        ai_response = "No response generated."
        
        # Find the last AI message that doesn't have tool calls (final response)
        for msg in reversed(messages):
            if (isinstance(msg, AIMessage) and 
                msg.content and 
                not msg.content.startswith("User Query:") and
                not (hasattr(msg, 'tool_calls') and msg.tool_calls)):
                ai_response = msg.content
                break
        
        # Check if response contains code blocks that should have been executed
        if self._contains_code_blocks(ai_response):
            logger.warning("Response contains code blocks without execution - this violates our rules!")
            # Force the agent to execute the code by setting goal_achieved to False
            state["goal_achieved"] = False
            state["current_step"] = "code_execution_required"
            # Don't return immediately - let the workflow continue to force code execution
            # Just log the violation and continue with the response formatting
            logger.warning("Code execution violation detected - continuing workflow to force execution")
        
        # Check if we have visualization config to convert to UI Resource
        visualization_config = state.get("visualization_config")
        query_results = state.get("query_results")
        
        # Safely handle reasoning field to prevent 'list' object has no attribute 'get' error
        reasoning_data = state.get("reasoning", [])
        if not isinstance(reasoning_data, list):
            logger.warning(f"Reasoning field is not a list: {type(reasoning_data)}, value: {reasoning_data}")
            reasoning_data = [str(reasoning_data)] if reasoning_data else []
        
        response_data = {
            "type": "text",
            "response": ai_response,
            "reasoning": " → ".join(reasoning_data),
            "sql_query": state.get("sql_query"),
            "data": query_results,
            "visualization": visualization_config,
            "current_step": state.get("current_step", "completed"),
            "goal_achieved": state.get("goal_achieved", False)
        }
        
        # Check for UI Resource in tool results (from visualization tools)
        ui_resource_from_tools = None
        tool_results = state.get("tool_results", [])
        if not isinstance(tool_results, list):
            logger.warning(f"Tool results is not a list: {type(tool_results)}, value: {tool_results}")
            tool_results = []
        
        for tool_result in tool_results:
            if isinstance(tool_result, dict) and "content" in tool_result:
                try:
                    # Parse the content (which is a JSON string from the tool)
                    content = json.loads(tool_result.get("content", "{}"))
                    
                    # Handle list content by converting to table UIResource
                    if isinstance(content, list) and len(content) > 0:
                        logger.info(f"Converting list data to table UIResource (rows: {len(content)})")
                        columns = list(content[0].keys()) if content else []
                        ui_resource = mcp_ui_generator.create_data_table_ui_resource(
                            content, 
                            columns, 
                            "Query Results"
                        )
                        ui_resource_from_tools = ui_resource
                        break
                    
                    # Ensure content is a dictionary for other processing
                    if not isinstance(content, dict):
                        logger.warning(f"Tool result content is not a dict: {type(content)}, value: {content}")
                        continue
                    
                    if content.get("type") == "ui_resource" and "ui_resource" in content:
                        ui_resource_from_tools = content.get("ui_resource")
                        if ui_resource_from_tools:
                            break
                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f"Failed to parse tool result content: {e}")
                    continue
        
        # Determine response type and generate UI Resource if appropriate
        if ui_resource_from_tools:
            # Use UI Resource from visualization tools
            response_data["type"] = "ui_resource"
            response_data["ui_resource"] = ui_resource_from_tools
            logger.info(f"Using UI Resource from visualization tool: {ui_resource_from_tools.get('uri', 'unknown')}")
        elif visualization_config:
            try:
                # Ensure visualization config data is JSON serializable
                safe_viz_config = ensure_json_serializable(visualization_config)
                
                # Convert VizroConfig to MCP UI Resource
                ui_resource = mcp_ui_generator.create_chart_ui_resource(
                    safe_viz_config, 
                    safe_viz_config.get("title", "Data Visualization")
                )
                response_data["type"] = "ui_resource"
                response_data["ui_resource"] = ui_resource
                logger.info(f"Generated UI Resource for visualization: {ui_resource.get('uri', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to generate UI Resource: {e}")
                response_data["type"] = "visualization"
        elif query_results and len(query_results) > 0:
            # If we have data but no visualization, create a table UI Resource
            try:
                # Ensure query results are JSON serializable
                safe_query_results = ensure_json_serializable(query_results)
                
                # Extract column names from the first row
                columns = list(safe_query_results[0].keys()) if safe_query_results else []
                ui_resource = mcp_ui_generator.create_data_table_ui_resource(
                    safe_query_results, 
                    columns, 
                    "Query Results"
                )
                response_data["type"] = "ui_resource"
                response_data["ui_resource"] = ui_resource
                logger.info(f"Generated UI Resource for data table: {ui_resource.get('uri', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to generate table UI Resource: {e}")
                response_data["type"] = "data"
        
        logger.info(f"Formatted final response: type={response_data['type']}, length={len(ai_response)}")
        return response_data
    
    def _contains_code_blocks(self, text: str) -> bool:
        """Check if text contains code blocks that should have been executed."""
        # Look for common code block patterns
        code_block_patterns = [
            r'```python\s*\n',  # Python code blocks
            r'```javascript\s*\n',  # JavaScript code blocks
            r'```js\s*\n',  # JS code blocks
            r'```java\s*\n',  # Java code blocks
            r'```cpp\s*\n',  # C++ code blocks
            r'```c\s*\n',  # C code blocks
            r'```go\s*\n',  # Go code blocks
            r'```rust\s*\n',  # Rust code blocks
            r'```r\s*\n',  # R code blocks
            r'```julia\s*\n',  # Julia code blocks
        ]
        
        import re
        for pattern in code_block_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    

    
    async def close(self):
        """Clean up resources."""
        if multi_mcp_manager:
            await multi_mcp_manager.close()
        self._initialized = False
        logger.info("LangGraph ReAct agent closed")
        
    async def clear_session_memory(self, session_id: str):
        """Clear memory for a specific session."""
        # Clear our backup memory system
        if session_id in self.session_histories:
            del self.session_histories[session_id]
            logger.info(f"🧠 MEMORY: Cleared backup memory for session {session_id}")
            
        # Try to clear the LangGraph memory
        if self.memory:
            try:
                # Create config for checkpointer
                config = {
                    "configurable": {"thread_id": session_id}
                }
                
                # Remove checkpoint if it exists
                await self.memory.adelete(config)
                logger.info(f"🧠 MEMORY: Cleared checkpoint memory for session {session_id}")
            except Exception as e:
                logger.warning(f"Failed to clear LangGraph memory for session {session_id}: {e}")
                
        return True


# Global agent instance
langgraph_agent = LangGraphReActAgent()
