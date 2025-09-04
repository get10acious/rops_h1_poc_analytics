# MCP Integration Guide

This guide provides comprehensive instructions for setting up and using Model Context Protocol (MCP) servers in the RewardOps Analytics POC project.

## 🎯 Overview

The MCP integration enables the system to use specialized tools for database operations and visualization generation. This guide covers:

- MCP server setup and configuration
- Database Toolbox integration
- Vizro MCP integration
- Client management and error handling
- Testing and validation

## 🏗️ Architecture

```
┌─────────────────┐    MCP Protocol    ┌─────────────────┐
│   Backend       │◄──────────────────►│   MCP Servers   │
│   (FastAPI)     │                    │                 │
│                 │                    │ • Database      │
│ MCP Client      │                    │   Toolbox       │
│ Manager         │                    │ • Vizro MCP     │
└─────────────────┘                    └─────────────────┘
```

## 🛠️ MCP Server Setup

### 1. Database Toolbox MCP

The Database Toolbox MCP provides SQL query execution capabilities for PostgreSQL databases.

#### Installation

```bash
# Install the MCP server
npm install -g @modelcontextprotocol/server-postgres

# Or use npx for direct execution
npx @modelcontextprotocol/server-postgres
```

#### Configuration

Create `backend/mcp_servers/database_config.json`:

```json
{
  "mcpServers": {
    "database": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://rewardops:password@localhost:5432/rewardops_db"
      }
    }
  }
}
```

#### Available Tools

- `db-toolbox:query` - Execute SQL queries
- `db-toolbox:get_schema` - Get database schema information
- `db-toolbox:list_tables` - List all tables in the database

### 2. Vizro MCP

The Vizro MCP provides visualization generation capabilities using the Vizro framework.

#### Installation

```bash
# Install the MCP server
npm install -g @modelcontextprotocol/server-vizro

# Or use npx for direct execution
npx @modelcontextprotocol/server-vizro
```

#### Configuration

Create `backend/mcp_servers/vizro_config.json`:

```json
{
  "mcpServers": {
    "vizro": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-vizro"],
      "env": {
        "VIZRO_CONFIG_PATH": "./vizro_config.json"
      }
    }
  }
}
```

#### Available Tools

- `vizro-mcp:create_dashboard` - Create interactive dashboards
- `vizro-mcp:create_chart` - Create individual charts
- `vizro-mcp:get_chart_types` - Get available chart types

## 🔧 Backend Integration

### 1. MCP Client Manager

Create `backend/mcp_multi_client.py`:

```python
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPClientManager:
    """Manages multiple MCP client connections."""
    
    def __init__(self):
        self.clients: Dict[str, ClientSession] = {}
        self.config_path = "mcp_servers/mcp_config.json"
    
    async def initialize(self) -> None:
        """Initialize all MCP clients."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            for server_name, server_config in config.get("mcpServers", {}).items():
                await self._create_client(server_name, server_config)
            
            logger.info(f"Initialized {len(self.clients)} MCP clients")
        except Exception as e:
            logger.error(f"Failed to initialize MCP clients: {e}")
            raise
    
    async def _create_client(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """Create a single MCP client."""
        try:
            server_params = StdioServerParameters(
                command=server_config["command"],
                args=server_config.get("args", []),
                env=server_config.get("env", {})
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    
                    # Store the client
                    self.clients[server_name] = session
                    
                    logger.info(f"Connected to MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Failed to create MCP client for {server_name}: {e}")
            raise
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a specific MCP server."""
        if server_name not in self.clients:
            raise ValueError(f"MCP server '{server_name}' not found")
        
        try:
            client = self.clients[server_name]
            result = await client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
            raise
    
    async def get_available_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Get available tools for a specific MCP server."""
        if server_name not in self.clients:
            raise ValueError(f"MCP server '{server_name}' not found")
        
        try:
            client = self.clients[server_name]
            tools = await client.list_tools()
            return tools.tools
        except Exception as e:
            logger.error(f"Failed to get tools for {server_name}: {e}")
            raise
    
    async def close_all(self) -> None:
        """Close all MCP client connections."""
        for server_name in list(self.clients.keys()):
            try:
                # MCP clients are automatically closed when exiting context managers
                del self.clients[server_name]
                logger.info(f"Closed MCP client: {server_name}")
            except Exception as e:
                logger.error(f"Error closing MCP client {server_name}: {e}")

# Global MCP client manager instance
mcp_manager = MCPClientManager()
```

### 2. Database Operations

Create `backend/database_operations.py`:

```python
import logging
from typing import List, Dict, Any, Optional
from mcp_multi_client import mcp_manager

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """Database operations using MCP Database Toolbox."""
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query using the Database Toolbox MCP.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of result dictionaries
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            arguments = {"query": query}
            if params:
                arguments["params"] = params
            
            result = await mcp_manager.call_tool("database", "db-toolbox:query", arguments)
            
            # Extract data from MCP response
            if "content" in result and result["content"]:
                return result["content"][0].get("text", [])
            
            return []
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    async def get_schema(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get database schema information.
        
        Args:
            table_name: Optional specific table name
            
        Returns:
            Schema information dictionary
        """
        try:
            arguments = {}
            if table_name:
                arguments["table"] = table_name
            
            result = await mcp_manager.call_tool("database", "db-toolbox:get_schema", arguments)
            
            if "content" in result and result["content"]:
                return result["content"][0].get("text", {})
            
            return {}
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            raise DatabaseError(f"Schema retrieval failed: {e}")
    
    async def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        try:
            result = await mcp_manager.call_tool("database", "db-toolbox:list_tables", {})
            
            if "content" in result and result["content"]:
                return result["content"][0].get("text", [])
            
            return []
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            raise DatabaseError(f"Table listing failed: {e}")
    
    async def get_merchants_by_redemption_volume(
        self, 
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get top merchants by redemption volume."""
        query = """
        SELECT 
            m.id,
            m.name,
            m.category,
            COUNT(r.id) as redemption_count,
            COALESCE(SUM(r.amount), 0) as total_volume,
            COALESCE(AVG(r.amount), 0) as avg_redemption_value
        FROM merchants m
        LEFT JOIN redemptions r ON m.id = r.merchant_id
        WHERE m.is_active = true
        """
        
        params = {}
        if start_date:
            query += " AND r.redemption_date >= %(start_date)s"
            params["start_date"] = start_date
        if end_date:
            query += " AND r.redemption_date <= %(end_date)s"
            params["end_date"] = end_date
            
        query += """
        GROUP BY m.id, m.name, m.category
        ORDER BY total_volume DESC NULLS LAST
        LIMIT %(limit)s
        """
        params["limit"] = limit
        
        return await self.execute_query(query, params)

# Global database operations instance
db_ops = DatabaseOperations()
```

### 3. Visualization Operations

Create `backend/visualization_operations.py`:

```python
import logging
from typing import List, Dict, Any, Optional
from mcp_multi_client import mcp_manager

logger = logging.getLogger(__name__)

class VisualizationOperations:
    """Visualization operations using Vizro MCP."""
    
    async def create_dashboard(
        self,
        title: str,
        data: List[Dict[str, Any]],
        chart_type: str = "bar",
        x_column: Optional[str] = None,
        y_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a dashboard using Vizro MCP.
        
        Args:
            title: Dashboard title
            data: Data to visualize
            chart_type: Type of chart (bar, line, pie, etc.)
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            
        Returns:
            Vizro dashboard configuration
        """
        try:
            # Auto-detect columns if not provided
            if not x_column and data:
                x_column = list(data[0].keys())[0]
            if not y_column and data:
                y_column = list(data[0].keys())[1] if len(data[0].keys()) > 1 else x_column
            
            arguments = {
                "title": title,
                "data": data,
                "chart_type": chart_type,
                "x_column": x_column,
                "y_column": y_column
            }
            
            result = await mcp_manager.call_tool("vizro", "vizro-mcp:create_dashboard", arguments)
            
            if "content" in result and result["content"]:
                return result["content"][0].get("text", {})
            
            return {}
        except Exception as e:
            logger.error(f"Dashboard creation failed: {e}")
            raise VisualizationError(f"Dashboard generation failed: {e}")
    
    async def create_chart(
        self,
        title: str,
        data: List[Dict[str, Any]],
        chart_type: str = "bar",
        x_column: Optional[str] = None,
        y_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a single chart using Vizro MCP.
        
        Args:
            title: Chart title
            data: Data to visualize
            chart_type: Type of chart (bar, line, pie, etc.)
            x_column: Column to use for x-axis
            y_column: Column to use for y-axis
            
        Returns:
            Vizro chart configuration
        """
        try:
            # Auto-detect columns if not provided
            if not x_column and data:
                x_column = list(data[0].keys())[0]
            if not y_column and data:
                y_column = list(data[0].keys())[1] if len(data[0].keys()) > 1 else x_column
            
            arguments = {
                "title": title,
                "data": data,
                "chart_type": chart_type,
                "x_column": x_column,
                "y_column": y_column
            }
            
            result = await mcp_manager.call_tool("vizro", "vizro-mcp:create_chart", arguments)
            
            if "content" in result and result["content"]:
                return result["content"][0].get("text", {})
            
            return {}
        except Exception as e:
            logger.error(f"Chart creation failed: {e}")
            raise VisualizationError(f"Chart generation failed: {e}")
    
    async def get_available_chart_types(self) -> List[str]:
        """
        Get available chart types from Vizro MCP.
        
        Returns:
            List of available chart types
        """
        try:
            result = await mcp_manager.call_tool("vizro", "vizro-mcp:get_chart_types", {})
            
            if "content" in result and result["content"]:
                return result["content"][0].get("text", [])
            
            return ["bar", "line", "pie", "scatter", "area"]
        except Exception as e:
            logger.error(f"Failed to get chart types: {e}")
            # Return default chart types if MCP call fails
            return ["bar", "line", "pie", "scatter", "area"]

# Global visualization operations instance
viz_ops = VisualizationOperations()
```

## 🧪 Testing MCP Integration

### 1. MCP Server Testing

Create `backend/test_mcp_integration.py`:

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from mcp_multi_client import mcp_manager
from database_operations import db_ops
from visualization_operations import viz_ops

@pytest.fixture
async def mock_mcp_manager():
    """Mock MCP manager for testing."""
    manager = AsyncMock()
    manager.call_tool.return_value = {
        "content": [{"text": [{"id": 1, "name": "Test Merchant", "volume": 1000}]}]
    }
    return manager

@pytest.mark.asyncio
async def test_database_query_execution(mock_mcp_manager):
    """Test database query execution through MCP."""
    with patch('database_operations.mcp_manager', mock_mcp_manager):
        result = await db_ops.execute_query("SELECT * FROM merchants LIMIT 5")
        
        assert result == [{"id": 1, "name": "Test Merchant", "volume": 1000}]
        mock_mcp_manager.call_tool.assert_called_once_with(
            "database", 
            "db-toolbox:query", 
            {"query": "SELECT * FROM merchants LIMIT 5"}
        )

@pytest.mark.asyncio
async def test_visualization_creation(mock_mcp_manager):
    """Test visualization creation through MCP."""
    mock_mcp_manager.call_tool.return_value = {
        "content": [{"text": {"title": "Test Chart", "type": "bar"}}]
    }
    
    with patch('visualization_operations.mcp_manager', mock_mcp_manager):
        data = [{"name": "Merchant A", "volume": 1000}]
        result = await viz_ops.create_chart("Test Chart", data, "bar")
        
        assert result == {"title": "Test Chart", "type": "bar"}
        mock_mcp_manager.call_tool.assert_called_once()

@pytest.mark.asyncio
async def test_merchants_by_redemption_volume(mock_mcp_manager):
    """Test merchants by redemption volume query."""
    mock_data = [
        {"id": 1, "name": "Merchant A", "total_volume": 5000},
        {"id": 2, "name": "Merchant B", "total_volume": 3000}
    ]
    mock_mcp_manager.call_tool.return_value = {
        "content": [{"text": mock_data}]
    }
    
    with patch('database_operations.mcp_manager', mock_mcp_manager):
        result = await db_ops.get_merchants_by_redemption_volume(limit=5)
        
        assert len(result) == 2
        assert result[0]["name"] == "Merchant A"
        assert result[0]["total_volume"] == 5000

@pytest.mark.asyncio
async def test_mcp_connection_failure():
    """Test handling of MCP connection failures."""
    with patch('mcp_multi_client.mcp_manager.call_tool') as mock_call:
        mock_call.side_effect = Exception("Connection failed")
        
        with pytest.raises(DatabaseError):
            await db_ops.execute_query("SELECT 1")
```

### 2. Integration Testing

Create `backend/test_mcp_integration_e2e.py`:

```python
import pytest
import asyncio
from mcp_multi_client import mcp_manager
from database_operations import db_ops
from visualization_operations import viz_ops

@pytest.mark.asyncio
async def test_end_to_end_analytics_flow():
    """Test complete analytics flow from query to visualization."""
    # This test requires actual MCP servers to be running
    
    # 1. Get merchants data
    merchants = await db_ops.get_merchants_by_redemption_volume(limit=5)
    assert len(merchants) > 0
    
    # 2. Create visualization
    chart_config = await viz_ops.create_chart(
        title="Top Merchants by Redemption Volume",
        data=merchants,
        chart_type="bar",
        x_column="name",
        y_column="total_volume"
    )
    
    assert "title" in chart_config
    assert chart_config["title"] == "Top Merchants by Redemption Volume"
    
    # 3. Verify chart configuration
    assert "data" in chart_config
    assert "chart_type" in chart_config
    assert chart_config["chart_type"] == "bar"

@pytest.mark.asyncio
async def test_mcp_server_availability():
    """Test that MCP servers are available and responding."""
    # Test database server
    tables = await db_ops.list_tables()
    assert "merchants" in tables
    assert "users" in tables
    assert "redemptions" in tables
    
    # Test vizro server
    chart_types = await viz_ops.get_available_chart_types()
    assert "bar" in chart_types
    assert "line" in chart_types
    assert "pie" in chart_types
```

## 🚀 Deployment and Configuration

### 1. Environment Variables

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql://rewardops:password@localhost:5432/rewardops_db
POSTGRES_CONNECTION_STRING=postgresql://rewardops:password@localhost:5432/rewardops_db

# MCP Configuration
MCP_DATABASE_CONFIG=mcp_servers/database_config.json
MCP_VIZRO_CONFIG=mcp_servers/vizro_config.json

# Logging
LOG_LEVEL=INFO
```

### 2. Docker Configuration

Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rewardops_db
      POSTGRES_USER: rewardops
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://rewardops:password@postgres:5432/rewardops_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
      - /var/run/docker.sock:/var/run/docker.sock

volumes:
  postgres_data:
```

### 3. Production Considerations

#### Security
- Use environment variables for sensitive configuration
- Implement proper authentication for MCP servers
- Use TLS for MCP communication in production
- Validate all inputs to prevent injection attacks

#### Performance
- Implement connection pooling for MCP clients
- Use caching for frequently accessed data
- Monitor MCP server performance
- Implement circuit breakers for fault tolerance

#### Monitoring
- Log all MCP tool calls and responses
- Monitor MCP server health
- Track query performance and errors
- Set up alerts for MCP server failures

## 🔧 Troubleshooting

### Common Issues

#### 1. MCP Server Connection Failures
```bash
# Check if MCP servers are running
ps aux | grep mcp

# Test MCP server connectivity
npx @modelcontextprotocol/server-postgres --help
npx @modelcontextprotocol/server-vizro --help

# Check configuration files
cat backend/mcp_servers/mcp_config.json
```

#### 2. Database Connection Issues
```bash
# Test database connection
psql postgresql://rewardops:password@localhost:5432/rewardops_db -c "SELECT 1"

# Check database logs
docker-compose logs postgres

# Verify database schema
psql postgresql://rewardops:password@localhost:5432/rewardops_db -c "\dt"
```

#### 3. Visualization Generation Failures
```bash
# Test Vizro MCP server
npx @modelcontextprotocol/server-vizro

# Check Vizro configuration
cat backend/mcp_servers/vizro_config.json

# Test with sample data
python -c "
import asyncio
from visualization_operations import viz_ops
data = [{'name': 'Test', 'value': 100}]
result = asyncio.run(viz_ops.create_chart('Test Chart', data))
print(result)
"
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('mcp').setLevel(logging.DEBUG)
```

## 📚 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Server Development Guide](https://github.com/modelcontextprotocol/servers)
- [Database Toolbox MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/database)
- [Vizro MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/vizro)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Vizro Documentation](https://vizro.mckinsey.com/)

This guide provides a comprehensive foundation for MCP integration. Follow these patterns and practices to ensure reliable and maintainable MCP server integration in your RewardOps Analytics POC.
