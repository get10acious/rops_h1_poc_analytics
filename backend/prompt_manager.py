"""
Prompt Manager for LangGraph ReAct Agent
Handles loading and formatting prompts from external files.
"""

import os
from typing import Dict, Any, List
from datetime import datetime


class PromptManager:
    """Manages prompts for the LangGraph ReAct agent."""
    
    def __init__(self, prompt_files_dir: str = None):
        """
        Initialize the prompt manager.
        
        Args:
            prompt_files_dir: Directory containing prompt files. Defaults to prompt_files in same directory.
        """
        if prompt_files_dir is None:
            # Default to prompt_files directory in the same directory as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_files_dir = os.path.join(current_dir, "prompt_files")
        
        self.prompt_files_dir = prompt_files_dir
        self._prompt_cache = {}
    
    def _load_prompt_file(self, filename: str) -> str:
        """Load a prompt from a file with caching."""
        if filename in self._prompt_cache:
            return self._prompt_cache[filename]
        
        file_path = os.path.join(self.prompt_files_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self._prompt_cache[filename] = content
                return content
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Prompt file not found: {file_path}") from exc
        except Exception as e:
            raise RuntimeError(f"Error loading prompt file {filename}: {e}") from e
    
    def get_base_system_prompt(self, 
                              conversation_context: str = "",
                              tools_list: str = "",
                              current_date: str = None) -> str:
        """
        Get the base system prompt with dynamic content.
        
        Args:
            conversation_context: Conversation memory context
            tools_list: List of available tools
            current_date: Current date (defaults to today)
            
        Returns:
            Formatted base system prompt
        """
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        base_prompt = self._load_prompt_file("base_system_prompt.txt")
        return base_prompt.format(
            conversation_context=conversation_context,
            tools_list=tools_list,
            current_date=current_date
        )
    
    def get_initial_process_instructions(self) -> str:
        """Get the initial process instructions for first iteration."""
        return self._load_prompt_file("initial_process_instructions.txt")
    
    def get_continuation_mode_instructions(self, 
                                         iteration_count: int,
                                         tool_results_count: int) -> str:
        """
        Get continuation mode instructions.
        
        Args:
            iteration_count: Current iteration number
            tool_results_count: Number of tool results from previous executions
            
        Returns:
            Formatted continuation mode instructions
        """
        instructions = self._load_prompt_file("continuation_mode_instructions.txt")
        return instructions.format(
            iteration_count=iteration_count,
            tool_results_count=tool_results_count
        )
    
    def get_conversation_memory_context(self, 
                                      message_count: int,
                                      previous_exchanges: int) -> str:
        """
        Get conversation memory context.
        
        Args:
            message_count: Total number of messages in conversation
            previous_exchanges: Number of previous exchanges
            
        Returns:
            Formatted conversation memory context
        """
        template = self._load_prompt_file("conversation_memory_template.txt")
        return template.format(
            message_count=message_count,
            previous_exchanges=previous_exchanges
        )
    
    def get_continuation_prompt(self, 
                              original_query: str,
                              tool_results: List[Dict[str, Any]]) -> str:
        """
        Build a continuation prompt based on tool results.
        
        Args:
            original_query: Original user query
            tool_results: Results from previous tool executions
            
        Returns:
            Formatted continuation prompt
        """
        # Build tool results summary
        results_summary = []
        has_errors = False
        has_successful_data = False
        
        for i, result in enumerate(tool_results):
            content_preview = str(result.get("content", ""))[:500]
            success = result.get("success", True)
            if not success:
                has_errors = True
                results_summary.append(f"Tool Result {i+1} (FAILED): {content_preview}")
            else:
                has_successful_data = True
                results_summary.append(f"Tool Result {i+1} (SUCCESS): {content_preview}")
        
        # Determine error guidance
        error_guidance = ""
        if has_errors and not has_successful_data:
            error_guidance = "⚠️ CRITICAL: Previous tool calls have FAILED with errors. DO NOT retry the same tool calls.\nInstead, provide a helpful response explaining what went wrong and suggest alternatives."
        elif has_errors:
            error_guidance = "⚠️ Some tool calls failed, but you have some successful data. Use the successful data to answer."
        
        # Load and format the continuation prompt template
        template = self._load_prompt_file("continuation_prompt_template.txt")
        return template.format(
            original_query=original_query,
            tool_results_summary='\n'.join(results_summary),
            error_guidance=error_guidance
        )
    
    def get_technical_issue_system_message(self) -> str:
        """Get system message for technical issues."""
        return "You are a helpful assistant that explains technical issues."
    
    def get_technical_issue_human_message(self, user_query: str) -> str:
        """Get human message for technical issues."""
        return f"""        
The user asked: '{user_query}'
But there were technical issues with the database tools. Please explain that there's a database connectivity or configuration issue and suggest they contact support.
"""
    
    def get_conversational_system_message(self) -> str:
        """Get system message for conversational responses."""
        return "You are a friendly and helpful analytics assistant. You have access to the full conversation history and can reference previous exchanges with the user."
    
    def get_fallback_response(self, user_query: str) -> str:
        """Get fallback response when no LLM is available."""
        return f"I understand you're asking: '{user_query}'. To provide detailed analytics, please configure a Google API key (GOOGLE_API_KEY) for enhanced AI processing with Gemini."
    
    def get_tool_execution_error_message(self, error_message: str) -> str:
        """Get error message for tool execution failures."""
        return f"Tool execution failed: {error_message}"
    
    def get_reasoning_error_message(self, error_message: str) -> str:
        """Get error message for reasoning failures."""
        return f"I encountered an error: {error_message}"
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._prompt_cache.clear()


# Global prompt manager instance
prompt_manager = PromptManager()
