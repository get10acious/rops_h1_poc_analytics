"""
LangGraph ReAct Agent for RewardOps Analytics POC.

This module implements a ReAct (Reasoning + Acting) agent that processes natural
language queries and orchestrates MCP tools to generate analytics responses.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime

from langgraph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from mcp_multi_client import mcp_manager
from database_operations import db_ops
from visualization_operations import viz_ops
from config import settings
from models.api import AgentState, AgentStep, AgentExecution

logger = logging.getLogger(__name__)

class ReActAgentState(TypedDict):
    """State for the ReAct agent."""
    query: str
    user_id: str
    reasoning: str
    action: str
    observation: str
    result: Dict[str, Any]
    error: str
    step_count: int
    max_steps: int
    timestamp: str

class ReActAgent:
    """ReAct agent for processing analytics queries."""
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.max_steps = 10
        self.system_prompt = self._create_system_prompt()
    
    def _initialize_llm(self):
        """Initialize the language model."""
        if settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=settings.OPENAI_API_KEY
            )
        elif settings.GEMINI_API_KEY:
            return ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=0.1,
                api_key=settings.GEMINI_API_KEY
            )
        else:
            logger.warning("No API key provided. Using mock LLM for development.")
            return None
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the ReAct agent."""
        return """
You are an intelligent analytics assistant for RewardOps, a loyalty and rewards platform.

Your role is to help business users analyze data by:
1. Understanding their natural language queries
2. Reasoning about what data they need
3. Using appropriate tools to retrieve and visualize data
4. Providing clear, actionable insights

Available tools:
- db-toolbox:query - Execute SQL queries on the RewardOps database
- db-toolbox:get_schema - Get database schema information
- vizro-mcp:create_chart - Create data visualizations
- vizro-mcp:create_dashboard - Create interactive dashboards

Database schema:
- merchants: id, name, category, description, website_url, logo_url, created_at, updated_at, is_active
- users: id, email, first_name, last_name, phone, date_of_birth, created_at, updated_at, is_active, total_points, tier
- redemptions: id, user_id, merchant_id, amount, points_used, redemption_date, status, transaction_id, notes, created_at
- campaigns: id, name, description, start_date, end_date, is_active, created_at
- user_campaigns: id, user_id, campaign_id, points_earned, participation_date

Follow the ReAct pattern:
1. REASON: Think about what the user is asking and what data you need
2. ACT: Use the appropriate tool to get the data
3. OBSERVE: Analyze the results and determine next steps
4. Repeat until you have a complete answer

Always provide helpful, accurate responses with proper visualizations when appropriate.
"""
    
    async def reason_about_query(self, state: ReActAgentState) -> ReActAgentState:
        """Reason about the user's query and determine what actions to take."""
        try:
            query = state["query"]
            step_count = state["step_count"]
            
            reasoning_prompt = f"""
Query: {query}
Step: {step_count + 1}

Based on the user's query, what do they want to know? What data do I need to retrieve?
What tools should I use?

Think step by step:
1. What is the user asking for?
2. What tables and columns do I need?
3. What type of visualization would be most helpful?
4. What SQL query should I write?

Provide your reasoning in 2-3 sentences.
"""
            
            if self.llm:
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=reasoning_prompt)
                ]
                response = await self.llm.ainvoke(messages)
                reasoning = response.content
            else:
                # Mock reasoning for development
                reasoning = f"User wants to analyze data related to: {query}. I need to query the database and create a visualization."
            
            state["reasoning"] = reasoning
            state["step_count"] += 1
            
            logger.info(f"Reasoning step {step_count + 1}: {reasoning}")
            return state
            
        except Exception as e:
            logger.error(f"Error in reasoning step: {e}")
            state["error"] = f"Reasoning failed: {str(e)}"
            return state
    
    async def execute_action(self, state: ReActAgentState) -> ReActAgentState:
        """Execute the determined action using MCP tools."""
        try:
            query = state["query"]
            reasoning = state["reasoning"]
            step_count = state["step_count"]
            
            # Determine action based on reasoning
            if "merchant" in query.lower() and "redemption" in query.lower():
                action = "query_merchants_by_redemption"
            elif "user" in query.lower() and "redemption" in query.lower():
                action = "query_users_by_redemption"
            elif "campaign" in query.lower():
                action = "query_campaigns"
            elif "trend" in query.lower() or "month" in query.lower():
                action = "query_trends"
            else:
                action = "general_query"
            
            # Execute the action
            if action == "query_merchants_by_redemption":
                result = await self._query_merchants_by_redemption(query)
            elif action == "query_users_by_redemption":
                result = await self._query_users_by_redemption(query)
            elif action == "query_campaigns":
                result = await self._query_campaigns(query)
            elif action == "query_trends":
                result = await self._query_trends(query)
            else:
                result = await self._general_query(query)
            
            state["action"] = action
            state["result"] = result
            state["step_count"] += 1
            
            logger.info(f"Action step {step_count + 1}: {action}")
            return state
            
        except Exception as e:
            logger.error(f"Error in action step: {e}")
            state["error"] = f"Action failed: {str(e)}"
            return state
    
    async def observe_result(self, state: ReActAgentState) -> ReActAgentState:
        """Observe the result and determine if more actions are needed."""
        try:
            result = state["result"]
            query = state["query"]
            step_count = state["step_count"]
            
            # Analyze the result
            if result.get("data") and len(result["data"]) > 0:
                # Data retrieved successfully, create visualization
                observation = f"Successfully retrieved {len(result['data'])} records. Creating visualization."
                
                # Create visualization
                visualization = await self._create_visualization(result["data"], query)
                result["visualization"] = visualization
                
                state["observation"] = observation
                state["result"] = result
                
                logger.info(f"Observation step {step_count + 1}: {observation}")
                return state
            else:
                # No data found
                observation = "No data found for the query. The user may need to adjust their parameters."
                state["observation"] = observation
                state["result"] = result
                
                logger.info(f"Observation step {step_count + 1}: {observation}")
                return state
                
        except Exception as e:
            logger.error(f"Error in observation step: {e}")
            state["error"] = f"Observation failed: {str(e)}"
            return state
    
    async def _query_merchants_by_redemption(self, query: str) -> Dict[str, Any]:
        """Query merchants by redemption volume."""
        try:
            # Extract limit from query if specified
            limit = 10
            if "top" in query.lower():
                import re
                match = re.search(r'top\s+(\d+)', query.lower())
                if match:
                    limit = int(match.group(1))
            
            # Extract date range if specified
            start_date = None
            end_date = None
            if "this month" in query.lower():
                from datetime import datetime, date
                today = date.today()
                start_date = date(today.year, today.month, 1).isoformat()
                end_date = today.isoformat()
            
            data = await db_ops.get_merchants_by_redemption_volume(
                limit=limit,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "data": data,
                "query_type": "merchants_by_redemption",
                "limit": limit,
                "date_range": {"start": start_date, "end": end_date}
            }
            
        except Exception as e:
            logger.error(f"Error querying merchants by redemption: {e}")
            return {"data": [], "error": str(e)}
    
    async def _query_users_by_redemption(self, query: str) -> Dict[str, Any]:
        """Query users by redemption activity."""
        try:
            # This would be implemented based on specific requirements
            # For now, return a placeholder
            return {
                "data": [],
                "query_type": "users_by_redemption",
                "message": "User redemption queries not yet implemented"
            }
            
        except Exception as e:
            logger.error(f"Error querying users by redemption: {e}")
            return {"data": [], "error": str(e)}
    
    async def _query_campaigns(self, query: str) -> Dict[str, Any]:
        """Query campaign data."""
        try:
            # This would be implemented based on specific requirements
            # For now, return a placeholder
            return {
                "data": [],
                "query_type": "campaigns",
                "message": "Campaign queries not yet implemented"
            }
            
        except Exception as e:
            logger.error(f"Error querying campaigns: {e}")
            return {"data": [], "error": str(e)}
    
    async def _query_trends(self, query: str) -> Dict[str, Any]:
        """Query trend data."""
        try:
            # This would be implemented based on specific requirements
            # For now, return a placeholder
            return {
                "data": [],
                "query_type": "trends",
                "message": "Trend queries not yet implemented"
            }
            
        except Exception as e:
            logger.error(f"Error querying trends: {e}")
            return {"data": [], "error": str(e)}
    
    async def _general_query(self, query: str) -> Dict[str, Any]:
        """Handle general queries."""
        try:
            # For general queries, try to get schema information
            tables = await db_ops.list_tables()
            
            return {
                "data": [{"table": table} for table in tables],
                "query_type": "general",
                "message": f"Available tables: {', '.join(tables)}"
            }
            
        except Exception as e:
            logger.error(f"Error in general query: {e}")
            return {"data": [], "error": str(e)}
    
    async def _create_visualization(self, data: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Create visualization for the data."""
        try:
            if not data:
                return {}
            
            # Determine chart type based on query
            chart_type = "bar"
            if "trend" in query.lower() or "over time" in query.lower():
                chart_type = "line"
            elif "category" in query.lower() or "distribution" in query.lower():
                chart_type = "pie"
            
            # Determine columns for visualization
            first_row = data[0]
            columns = list(first_row.keys())
            
            x_column = None
            y_column = None
            
            # Try to find appropriate columns
            for col in columns:
                if col in ["name", "merchant_name", "category"]:
                    x_column = col
                elif col in ["total_volume", "amount", "count", "redemption_count"]:
                    y_column = col
            
            # Fallback to first two columns
            if not x_column and len(columns) > 0:
                x_column = columns[0]
            if not y_column and len(columns) > 1:
                y_column = columns[1]
            
            # Create chart
            chart_config = await viz_ops.create_chart(
                title=f"Analytics: {query[:50]}...",
                data=data,
                chart_type=chart_type,
                x_column=x_column,
                y_column=y_column
            )
            
            return chart_config
            
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            return {"error": str(e)}
    
    def should_continue(self, state: ReActAgentState) -> str:
        """Determine if the agent should continue or end."""
        if state.get("error"):
            return "end"
        
        if state["step_count"] >= state["max_steps"]:
            return "end"
        
        if state.get("result") and state["result"].get("data"):
            return "end"
        
        return "continue"
    
    async def run(self, query: str, user_id: str) -> Dict[str, Any]:
        """Run the ReAct agent for a given query."""
        start_time = time.time()
        
        try:
            # Initialize state
            state = ReActAgentState(
                query=query,
                user_id=user_id,
                reasoning="",
                action="",
                observation="",
                result={},
                error="",
                step_count=0,
                max_steps=self.max_steps,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # Run the agent workflow
            while state["step_count"] < state["max_steps"] and not state.get("error"):
                # Reason
                state = await self.reason_about_query(state)
                if state.get("error"):
                    break
                
                # Act
                state = await self.execute_action(state)
                if state.get("error"):
                    break
                
                # Observe
                state = await self.observe_result(state)
                if state.get("error"):
                    break
                
                # Check if we should continue
                if self.should_continue(state) == "end":
                    break
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Return final result
            return {
                "data": state["result"].get("data", []),
                "visualization": state["result"].get("visualization", {}),
                "query": query,
                "query_id": f"query_{int(time.time())}",
                "processing_time": processing_time,
                "steps": state["step_count"],
                "error": state.get("error"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error running ReAct agent: {e}")
            return {
                "data": [],
                "visualization": {},
                "query": query,
                "query_id": f"query_{int(time.time())}",
                "processing_time": time.time() - start_time,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

def create_react_agent() -> ReActAgent:
    """Create and return a ReAct agent instance."""
    return ReActAgent()
