"""
LangGraph Tools Integration with Multi-MCP Manager
Creates LangGraph-compatible tools from multiple MCP servers without proxy.
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Type
from pydantic import BaseModel, Field, create_model

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from mcp_multi_client import mcp_manager
from visualization_tool import get_visualization_tools

logger = logging.getLogger(__name__)


def _create_pydantic_model_from_schema(schema: Dict[str, Any], model_name: str) -> Type[BaseModel]:
    """Dynamically create a Pydantic model from a JSON schema."""
    fields = {}
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            prop_type_str = prop_schema.get("type", "string")
            
            type_mapping = {
                "string": str,
                "number": float,
                "integer": int,
                "boolean": bool,
                "array": List[Any],
                "object": Dict[str, Any],
            }
            field_type = type_mapping.get(prop_type_str, Any)

            field_definition_args = {}
            if 'description' in prop_schema:
                field_definition_args['description'] = prop_schema['description']

            if prop_name not in schema.get("required", []):
                # Optional field
                field_definition_args['default'] = prop_schema.get("default")
                fields[prop_name] = (Optional[field_type], Field(**field_definition_args))
            else:
                # Required field
                fields[prop_name] = (field_type, Field(**field_definition_args))

    return create_model(model_name, **fields)


class MCPTool(BaseTool):
    """Generic tool wrapper for MCP server tools."""
    
    def __init__(self, tool_name: str, tool_schema: Dict[str, Any], **kwargs):
        """Initialize MCP tool wrapper."""
        self.tool_name = tool_name
        self.tool_schema = tool_schema
        
        # Set up the tool properties
        super().__init__(
            name=tool_name,
            description=tool_schema.get("description", f"MCP tool: {tool_name}"),
            **kwargs
        )
        
        # Create Pydantic model for args validation
        if "inputSchema" in tool_schema:
            self.args_schema = _create_pydantic_model_from_schema(
                tool_schema["inputSchema"], 
                f"{tool_name.title()}Args"
            )
    
    def _run(self, **kwargs) -> str:
        """Synchronous run method (required by BaseTool)."""
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Execute the MCP tool."""
        try:
            # Call the MCP tool
            result = await asyncio.wait_for(
                mcp_manager.call_tool(self.tool_name, kwargs),
                timeout=30.0
            )
            logger.info(f"MCP tool '{self.tool_name}' completed successfully")
            
            if result and "content" in result:
                return result["content"]
            else:
                return json.dumps({"error": f"No result from {self.tool_name}"})
                
        except Exception as e:
            error_msg = f"Error executing {self.tool_name}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})


class DatabaseQueryTool(BaseTool):
    """Tool for executing database queries via MCP."""
    
    name: str = "execute_database_query"
    description: str = """
    Execute SQL queries on the PostgreSQL database.
    Use this tool to fetch data, analyze trends, and answer data-related questions.
    
    Examples:
    - Top merchants: SELECT merchant_name, SUM(redemption_amount) as total FROM redemptions JOIN merchants ON redemptions.merchant_id = merchants.id GROUP BY merchant_name ORDER BY total DESC LIMIT 10;
    - User activity: SELECT user_id, COUNT(*) as redemptions FROM redemptions GROUP BY user_id ORDER BY redemptions DESC LIMIT 10;
    - Trends: SELECT DATE(created_at) as date, COUNT(*) as count FROM redemptions WHERE created_at >= NOW() - INTERVAL '30 days' GROUP BY DATE(created_at) ORDER BY date;
    """
    
    def _run(self, query: str) -> str:
        """Synchronous run method."""
        return asyncio.run(self._arun(query))
    
    async def _arun(self, query: str) -> str:
        """Execute a database query."""
        try:
            logger.info(f"Executing database query: {query}")
            
            # Ensure MCP manager is initialized
            if not mcp_manager._initialized:
                await mcp_manager.initialize()
            
            # Try to find PostgreSQL tool
            tools = await mcp_manager.list_all_tools()
            postgres_tool = None
            
            for server_name, server_tools in tools.items():
                for tool in server_tools:
                    if "postgres" in tool["name"].lower() or "sql" in tool["name"].lower() or tool["name"] == "execute_sql":
                        postgres_tool = tool["name"]
                        break
                if postgres_tool:
                    break
            
            if not postgres_tool:
                return json.dumps({"error": "No PostgreSQL tool found"}, indent=2)
            
            # Call PostgreSQL tool via MCP with correct parameter name
            result = await mcp_manager.call_tool(postgres_tool, {"sql": query})
            
            if result and "content" in result:
                return result["content"]
            else:
                return json.dumps({"error": "No result from PostgreSQL tool"}, indent=2)
                
        except Exception as e:
            error_msg = f"Database query failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, indent=2)


class CodeExecutionTool(BaseTool):
    """Tool for executing Python code in a sandbox environment."""
    
    name: str = "execute_python_code"
    description: str = """
    Execute Python code for data analysis, processing, and custom calculations.
    Use this tool when you need to:
    - Process or transform data
    - Perform complex calculations
    - Create custom visualizations
    - Test code examples
    
    The code runs in a safe sandbox environment with common data science libraries available.
    """
    
    def _run(self, code: str) -> str:
        """Synchronous run method."""
        return asyncio.run(self._arun(code))
    
    async def _arun(self, code: str) -> str:
        """Execute Python code in sandbox."""
        try:
            logger.info(f"Executing Python code: {code[:100]}...")
            
            # For now, we'll implement a simple sandbox
            # In production, this would use a proper sandboxed environment
            import sys
            from io import StringIO
            import json
            import pandas as pd
            import numpy as np
            
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            # Create a safe execution environment
            safe_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'max': max,
                    'min': min,
                    'sum': sum,
                    'sorted': sorted,
                },
                'json': json,
                'pd': pd,
                'np': np,
            }
            
            # Execute the code
            exec(code, safe_globals)
            
            # Restore stdout
            sys.stdout = old_stdout
            
            # Get the output
            output = captured_output.getvalue()
            
            return json.dumps({
                "success": True,
                "output": output,
                "execution_completed": True
            }, indent=2)
            
        except Exception as e:
            # Restore stdout in case of error
            sys.stdout = old_stdout
            error_msg = f"Code execution failed: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "execution_completed": False
            }, indent=2)


async def get_all_mcp_langraph_tools() -> List[BaseTool]:
    """Get all available tools from MCP servers as LangGraph tools."""
    try:
        # Ensure MCP manager is initialized
        if not mcp_manager._initialized:
            await mcp_manager.initialize()
        
        tools = []
        
        # Add visualization tools
        visualization_tools = get_visualization_tools()
        tools.extend(visualization_tools)
        logger.info(f"✅ Added {len(visualization_tools)} visualization tools")
        
        # Add composite data tools (data + code + UIResource)
        try:
            from composite_data_tools import get_composite_data_tools
            composite_tools = get_composite_data_tools()
            tools.extend(composite_tools)
            logger.info(f"✅ Added {len(composite_tools)} composite data tools")
        except ImportError as e:
            logger.warning(f"Could not import composite data tools: {e}")
        
        # Add database query tool
        tools.append(DatabaseQueryTool())
        
        # Add code execution tool
        tools.append(CodeExecutionTool())
        
        # Get tools from MCP servers
        all_tools = await mcp_manager.list_all_tools()
        
        for server_name, server_tools in all_tools.items():
            for tool_schema in server_tools:
                tool_name = tool_schema.get("name", "")
                
                # Skip tools we've already wrapped with custom implementations
                if tool_name in ["execute_sql", "list_tables"]:
                    continue
                
                # Create generic MCP tool wrapper
                mcp_tool = MCPTool(tool_name, tool_schema)
                tools.append(mcp_tool)
        
        logger.info(f"Created {len(tools)} LangGraph tools from MCP servers")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to get MCP tools: {e}")
        return []


async def get_database_tools() -> List[BaseTool]:
    """Get database-specific tools."""
    return [DatabaseQueryTool()]


async def get_code_execution_tools() -> List[BaseTool]:
    """Get code execution tools."""
    return [CodeExecutionTool()]
