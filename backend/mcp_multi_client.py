"""
MCP Multi-Client Manager for RewardOps Analytics POC.

This module manages multiple MCP (Model Context Protocol) client connections
and provides a unified interface for tool calls across different MCP servers.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPClientManager:
    """Manages multiple MCP client connections."""
    
    def __init__(self):
        self.clients: Dict[str, ClientSession] = {}
        self.config_path = "mcp_servers/mcp_config.json"
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize all MCP clients."""
        if self.initialized:
            logger.info("MCP clients already initialized")
            return
        
        try:
            # Load configuration
            config = self._load_config()
            
            # Initialize each MCP server
            for server_name, server_config in config.get("mcpServers", {}).items():
                await self._create_client(server_name, server_config)
            
            self.initialized = True
            logger.info(f"Initialized {len(self.clients)} MCP clients: {list(self.clients.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP clients: {e}")
            raise
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP configuration from file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"MCP config file not found: {self.config_path}")
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Loaded MCP configuration from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading MCP configuration: {e}")
            raise
    
    async def _create_client(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """Create a single MCP client."""
        try:
            logger.info(f"Creating MCP client for {server_name}")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=server_config["command"],
                args=server_config.get("args", []),
                env=server_config.get("env", {})
            )
            
            # Create client connection
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    
                    # Store the client (note: this is a simplified approach)
                    # In a real implementation, you'd need to manage the connection lifecycle
                    self.clients[server_name] = session
                    
                    logger.info(f"Successfully connected to MCP server: {server_name}")
                    
        except Exception as e:
            logger.error(f"Failed to create MCP client for {server_name}: {e}")
            raise
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a specific MCP server."""
        if not self.initialized:
            raise RuntimeError("MCP clients not initialized. Call initialize() first.")
        
        if server_name not in self.clients:
            raise ValueError(f"MCP server '{server_name}' not found. Available servers: {list(self.clients.keys())}")
        
        try:
            client = self.clients[server_name]
            logger.debug(f"Calling tool {tool_name} on server {server_name} with args: {arguments}")
            
            # Call the tool
            result = await client.call_tool(tool_name, arguments)
            
            logger.debug(f"Tool {tool_name} on server {server_name} returned: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
            raise
    
    async def get_available_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Get available tools for a specific MCP server."""
        if not self.initialized:
            raise RuntimeError("MCP clients not initialized. Call initialize() first.")
        
        if server_name not in self.clients:
            raise ValueError(f"MCP server '{server_name}' not found. Available servers: {list(self.clients.keys())}")
        
        try:
            client = self.clients[server_name]
            tools = await client.list_tools()
            
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                for tool in tools.tools
            ]
            
        except Exception as e:
            logger.error(f"Failed to get tools for {server_name}: {e}")
            raise
    
    async def get_server_info(self, server_name: str) -> Dict[str, Any]:
        """Get information about a specific MCP server."""
        if not self.initialized:
            raise RuntimeError("MCP clients not initialized. Call initialize() first.")
        
        if server_name not in self.clients:
            raise ValueError(f"MCP server '{server_name}' not found. Available servers: {list(self.clients.keys())}")
        
        try:
            client = self.clients[server_name]
            info = await client.get_server_info()
            
            return {
                "name": info.name,
                "version": info.version,
                "protocol_version": info.protocolVersion
            }
            
        except Exception as e:
            logger.error(f"Failed to get server info for {server_name}: {e}")
            raise
    
    def get_available_servers(self) -> List[str]:
        """Get list of available MCP servers."""
        return list(self.clients.keys())
    
    def is_initialized(self) -> bool:
        """Check if MCP clients are initialized."""
        return self.initialized
    
    async def close_all(self) -> None:
        """Close all MCP client connections."""
        if not self.initialized:
            return
        
        logger.info("Closing all MCP client connections...")
        
        for server_name in list(self.clients.keys()):
            try:
                # In a real implementation, you'd properly close the connections
                # For now, we'll just remove them from the dictionary
                del self.clients[server_name]
                logger.info(f"Closed MCP client: {server_name}")
                
            except Exception as e:
                logger.error(f"Error closing MCP client {server_name}: {e}")
        
        self.initialized = False
        logger.info("All MCP client connections closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all MCP servers."""
        health_status = {
            "overall_status": "healthy",
            "servers": {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        for server_name in self.clients.keys():
            try:
                # Try to get server info as a health check
                info = await self.get_server_info(server_name)
                health_status["servers"][server_name] = {
                    "status": "healthy",
                    "info": info
                }
                
            except Exception as e:
                health_status["servers"][server_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
        
        return health_status

# Global MCP client manager instance
mcp_manager = MCPClientManager()

# Convenience functions for backward compatibility
async def call_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to call MCP tools."""
    return await mcp_manager.call_tool(server_name, tool_name, arguments)

async def get_mcp_tools(server_name: str) -> List[Dict[str, Any]]:
    """Convenience function to get MCP tools."""
    return await mcp_manager.get_available_tools(server_name)

async def initialize_mcp_clients() -> None:
    """Convenience function to initialize MCP clients."""
    await mcp_manager.initialize()

async def close_mcp_clients() -> None:
    """Convenience function to close MCP clients."""
    await mcp_manager.close_all()
