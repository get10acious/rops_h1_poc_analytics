"""
Multi-MCP Client Manager for Backend
Directly connects to multiple MCP servers without proxy, inspired by mcp_manager and dev_assistant_agent.
"""

import asyncio
import logging
import os
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone

# Use fastmcp for better async support like in mcp_manager
from fastmcp.client import StdioTransport, Client as FastMCPClient
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    name: str
    enabled: bool = True
    connection_type: str = "stdio"  # "stdio" or "url"
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env_vars: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None
    description: str = ""
    max_reconnect_attempts: int = 3
    reconnect_delay_seconds: int = 5


class MCPClientWrapper:
    """Wrapper for a single MCP client connection."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.status = "disconnected"
        self._transport: Optional[StdioTransport] = None
        self._client: Optional[FastMCPClient] = None
        self._tools_cache: List[Dict[str, Any]] = []
        self.last_heartbeat: Optional[datetime] = None
        self.reconnect_attempts = 0
    
    
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            logger.info(f"Connecting to MCP server: {self.config.name}")
            self.status = "connecting"
            
            if self.config.connection_type == "stdio":
                if not self.config.command:
                    raise ValueError(f"Command required for stdio connection: {self.config.name}")
                
                # Set up environment
                env = os.environ.copy()
                env.update(self.config.env_vars)
                
                # Create StdioTransport
                self._transport = StdioTransport(
                    command=self.config.command,
                    args=self.config.args,
                    env=env
                )
                
                # Test connection by listing tools
                async with self._transport.connect_session() as session:
                    tools_response = await session.list_tools()
                    self._tools_cache = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": getattr(tool, 'inputSchema', {})
                        }
                        for tool in tools_response.tools
                    ]
                
                logger.info(f"Connected to {self.config.name}: {len(self._tools_cache)} tools available")
                
            elif self.config.connection_type == "url":
                if not self.config.url:
                    raise ValueError(f"URL required for url connection: {self.config.name}")
                
                # Create HTTP client
                self._client = FastMCPClient(base_url=self.config.url)
                
                # Test connection
                async with self._client:
                    tools_response = await self._client.list_tools()
                    self._tools_cache = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": getattr(tool, 'inputSchema', {})
                        }
                        for tool in tools_response.tools
                    ]
                
                logger.info(f"Connected to {self.config.name} via URL: {len(self._tools_cache)} tools available")
            
            else:
                raise ValueError(f"Unsupported connection type: {self.config.connection_type}")
            
            self.status = "connected"
            self.last_heartbeat = datetime.now(timezone.utc)
            self.reconnect_attempts = 0
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.config.name}: {e}")
            self.status = "error"
            await self._cleanup()
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        logger.info(f"Disconnecting from {self.config.name}")
        await self._cleanup()
        self.status = "disconnected"
        self.reconnect_attempts = 0
    
    async def _cleanup(self):
        """Clean up resources."""
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception as e:
                logger.debug(f"Error closing client for {self.config.name}: {e}")
            self._client = None
        
        self._transport = None
    
    async def ensure_connected(self) -> bool:
        """Ensure the connection is active, reconnect if needed."""
        if self.status == "connected":
            return True
        
        if self.status in ["connecting", "reconnecting"]:
            return False
        
        if self.reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for {self.config.name}")
            return False
        
        logger.info(f"Attempting to reconnect to {self.config.name} (attempt {self.reconnect_attempts + 1})")
        self.status = "reconnecting"
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts > 1:
            await asyncio.sleep(self.config.reconnect_delay_seconds)
        
        return await self.connect()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from this server."""
        if not await self.ensure_connected():
            return []
        
        try:
            # Use cached tools if available
            if self._tools_cache:
                return self._tools_cache
            
            if self.config.connection_type == "stdio" and self._transport:
                async with self._transport.connect_session() as session:
                    tools_response = await session.list_tools()
                    self._tools_cache = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": getattr(tool, 'inputSchema', {}),
                            "server": self.config.name
                        }
                        for tool in tools_response.tools
                    ]
            
            elif self.config.connection_type == "url" and self._client:
                async with self._client:
                    tools_response = await self._client.list_tools()
                    self._tools_cache = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": getattr(tool, 'inputSchema', {}),
                            "server": self.config.name
                        }
                        for tool in tools_response.tools
                    ]
            
            self.last_heartbeat = datetime.now(timezone.utc)
            return self._tools_cache
            
        except Exception as e:
            logger.error(f"Error listing tools from {self.config.name}: {e}")
            self.status = "error"
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a tool on this server."""
        if not await self.ensure_connected():
            return None
        
        try:
            logger.debug(f"Calling tool '{tool_name}' on {self.config.name} with args: {arguments}")
            
            result = None
            if self.config.connection_type == "stdio" and self._transport:
                async with self._transport.connect_session() as session:
                    response = await session.call_tool(name=tool_name, arguments=arguments)
                    
                    if hasattr(response, 'content') and response.content:
                        if isinstance(response.content, list) and len(response.content) > 0:
                            # Handle multiple content items
                            if len(response.content) > 1:
                                # Multiple results - combine them
                                all_results = []
                                for content_item in response.content:
                                    if hasattr(content_item, 'text'):
                                        all_results.append(content_item.text)
                                    else:
                                        all_results.append(str(content_item))
                                result = {"content": "\n".join(all_results), "type": "text"}
                            else:
                                # Single result
                                content_item = response.content[0]
                                if hasattr(content_item, 'text'):
                                    result = {"content": content_item.text, "type": "text"}
                                else:
                                    result = {"content": str(content_item), "type": "text"}
                        else:
                            result = {"content": str(response.content), "type": "text"}
                    else:
                        result = {"content": str(response), "type": "text"}
            
            elif self.config.connection_type == "url" and self._client:
                async with self._client:
                    response = await self._client.call_tool(name=tool_name, arguments=arguments)
                    
                    if hasattr(response, 'content') and response.content:
                        if isinstance(response.content, list) and len(response.content) > 0:
                            # Handle multiple content items
                            if len(response.content) > 1:
                                # Multiple results - combine them
                                all_results = []
                                for content_item in response.content:
                                    if hasattr(content_item, 'text'):
                                        all_results.append(content_item.text)
                                    else:
                                        all_results.append(str(content_item))
                                result = {"content": "\n".join(all_results), "type": "text"}
                            else:
                                # Single result
                                content_item = response.content[0]
                                if hasattr(content_item, 'text'):
                                    result = {"content": content_item.text, "type": "text"}
                                else:
                                    result = {"content": str(content_item), "type": "text"}
                        else:
                            result = {"content": str(response.content), "type": "text"}
                    else:
                        result = {"content": str(response), "type": "text"}
            
            self.last_heartbeat = datetime.now(timezone.utc)
            logger.debug(f"Tool '{tool_name}' result from {self.config.name}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}' on {self.config.name}: {e}")
            self.status = "error"
            return None


class MultiMCPManager:
    """Manages multiple MCP server connections directly."""
    
    def __init__(self):
        self.clients: Dict[str, MCPClientWrapper] = {}
        self.configs: List[MCPServerConfig] = []
        self._initialized = False
        self._lock = asyncio.Lock()
    
    def add_server_config(self, config: MCPServerConfig):
        """Add a server configuration."""
        self.configs.append(config)
        if config.enabled:
            self.clients[config.name] = MCPClientWrapper(config)
            logger.info(f"Added MCP server config: {config.name}")
    
    def load_configs_from_file(self, config_file: str = None):
        """Load MCP server configurations from JSON file."""
        if config_file is None:
            config_file = Path(__file__).parent / "mcp_servers" / "mcp_config.json"
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Handle both old and new config formats
            if "mcpServers" in config_data:
                # Old format from rops_h1_poc_analytics
                servers = config_data.get("mcpServers", {})
                for server_name, server_config in servers.items():
                    config = MCPServerConfig(
                        name=server_name,
                        enabled=True,
                        connection_type="stdio",
                        command=server_config.get("command"),
                        args=server_config.get("args", []),
                        env_vars=server_config.get("env", {}),
                        description=f"MCP Server: {server_name}"
                    )
                    self.add_server_config(config)
            else:
                # New format from mcpui-sandbox-chat
                servers = config_data.get("servers", [])
                for server_data in servers:
                    # Resolve environment variables in env_vars
                    env_vars = server_data.get("env_vars", {})
                    for key, value in env_vars.items():
                        if isinstance(value, str) and value.startswith("$"):
                            # Environment variable reference
                            env_var_name = value[1:]
                            env_vars[key] = os.getenv(env_var_name, "")
                        elif isinstance(value, str) and not value:
                            # Empty string, try to get from environment with same name
                            env_vars[key] = os.getenv(key, "")
                    
                    server_data["env_vars"] = env_vars
                    
                    # Skip GitHub if no token available
                    if server_data["name"] == "github" and not env_vars.get("GITHUB_PERSONAL_ACCESS_TOKEN"):
                        logger.info("Skipping GitHub MCP server - no GITHUB_PERSONAL_ACCESS_TOKEN available")
                        continue
                    
                    config = MCPServerConfig(**server_data)
                    self.add_server_config(config)
                
            logger.info(f"Loaded {len(self.configs)} MCP server configurations from {config_file}")
            
        except FileNotFoundError:
            logger.warning(f"MCP config file {config_file} not found, loading default configs")
            self.load_default_configs()
        except Exception as e:
            logger.error(f"Error loading MCP config from {config_file}: {e}")
            self.load_default_configs()
    
    def load_default_configs(self):
        """Load default MCP server configurations."""
        # PostgreSQL Toolbox
        postgres_config = MCPServerConfig(
            name="database",
            enabled=True,
            connection_type="stdio",
            command="npx",
            args=["@modelcontextprotocol/server-postgres"],
            env_vars={
                "POSTGRES_CONNECTION_STRING": "postgresql://analytics:password@localhost:5432/analytics_db"
            },
            description="PostgreSQL database operations"
        )
        self.add_server_config(postgres_config)
        
        # UI Generator (built-in)
        # No need for external UI server since we use mcp_ui_generator.py directly
    
    async def initialize(self) -> bool:
        """Initialize all MCP client connections."""
        if self._initialized:
            return True
        
        if not self.configs:
            self.load_configs_from_file()
        
        logger.info(f"Initializing {len(self.clients)} MCP clients...")
        
        # Connect to all enabled servers
        connection_tasks = []
        for client in self.clients.values():
            connection_tasks.append(client.connect())
        
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        successful_connections = 0
        for client, result in zip(self.clients.values(), results):
            if isinstance(result, Exception):
                logger.error(f"Error connecting to {client.config.name}: {result}")
            elif result:
                successful_connections += 1
        
        self._initialized = successful_connections > 0
        logger.info(f"MCP initialization complete: {successful_connections}/{len(self.clients)} servers connected")
        return self._initialized
    
    async def disconnect_all(self):
        """Disconnect from all servers."""
        logger.info("Disconnecting from all MCP servers...")
        
        disconnect_tasks = []
        for client in self.clients.values():
            disconnect_tasks.append(client.disconnect())
        
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        self._initialized = False
        logger.info("All MCP connections closed")
    
    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all tools from all connected servers."""
        if not self._initialized:
            await self.initialize()
        
        all_tools = {}
        for server_name, client in self.clients.items():
            tools = await client.list_tools()
            all_tools[server_name] = tools
        
        return all_tools
    
    async def get_tool_by_name(self, tool_name: str) -> Optional[tuple[MCPClientWrapper, Dict[str, Any]]]:
        """Find a tool by name across all servers."""
        all_tools = await self.list_all_tools()
        
        for server_name, tools in all_tools.items():
            for tool in tools:
                if tool["name"] == tool_name:
                    return self.clients[server_name], tool
        
        return None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a tool by name, automatically finding the right server."""
        async with self._lock:
            tool_info = await self.get_tool_by_name(tool_name)
            
            if not tool_info:
                logger.error(f"Tool '{tool_name}' not found in any connected server")
                return None
            
            client, tool_schema = tool_info
            result = await client.call_tool(tool_name, arguments)
            
            if result:
                result["server"] = client.config.name
                result["tool"] = tool_name
            
            return result
    
    async def get_server_status(self) -> Dict[str, str]:
        """Get status of all servers."""
        return {name: client.status for name, client in self.clients.items()}
    
    async def health_check(self):
        """Perform health check on all servers."""
        logger.debug("Performing health check on all MCP servers")
        
        for client in self.clients.values():
            if client.status == "connected":
                tools = await client.list_tools()
                if not tools and client.status == "connected":
                    logger.warning(f"Health check failed for {client.config.name}")

    # Legacy compatibility methods
    async def get_available_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Get available tools for a specific MCP server (legacy compatibility)."""
        if server_name in self.clients:
            return await self.clients[server_name].list_tools()
        return []
    
    def get_available_servers(self) -> List[str]:
        """Get list of available MCP servers."""
        return list(self.clients.keys())
    
    def is_initialized(self) -> bool:
        """Check if MCP clients are initialized."""
        return self._initialized
    
    async def close_all(self) -> None:
        """Close all MCP client connections (legacy compatibility)."""
        await self.disconnect_all()


# Global multi-MCP manager instance
mcp_manager = MultiMCPManager()

# Convenience functions for backward compatibility
async def call_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to call MCP tools."""
    return await mcp_manager.call_tool(tool_name, arguments)

async def get_mcp_tools(server_name: str) -> List[Dict[str, Any]]:
    """Convenience function to get MCP tools."""
    return await mcp_manager.get_available_tools(server_name)

async def initialize_mcp_clients() -> None:
    """Convenience function to initialize MCP clients."""
    await mcp_manager.initialize()

async def close_mcp_clients() -> None:
    """Convenience function to close MCP clients."""
    await mcp_manager.close_all()
