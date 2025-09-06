# AI Director's Guide: RewardOps Analytics POC

## 🎯 Complete System Architecture Guide for AI-Assisted Development

This guide provides comprehensive instructions for using AI development tools (Cursor, GitHub Copilot, etc.) to build the RewardOps Analytics POC. Follow this step-by-step approach to build each component systematically.

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [LangGraph ReAct Agent](#langgraph-react-agent)
4. [MCP Server Integration](#mcp-server-integration)
5. [Frontend Components](#frontend-components)
6. [Database Schema](#database-schema)
7. [Development Workflow](#development-workflow)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Guide](#deployment-guide)

## 🏗️ System Overview

### Business Context
Transform a static admin homepage into an intelligent analytics dashboard where business users can ask natural language questions like "Show me top merchants by redemption volume" and receive real-time interactive visualizations.

### Technical Stack
```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   React/Next.js │◄───────────────►│   FastAPI       │
│   Frontend      │                 │   Backend       │
│                 │                 │                 │
│ • Chat UI       │                 │ • ReAct Agent   │
│ • Vizro Charts  │                 │ • MCP Manager   │
│ • WebSocket     │                 │ • WebSocket     │
└─────────────────┘                 └─────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │   MCP Servers   │
                                    │                 │
                                    │ • Database      │
                                    │   Toolbox       │
                                    │ • Vizro MCP     │
                                    │ • Code Sandbox  │
                                    └─────────────────┘
```

### Core Data Flow
1. **User Input**: Natural language query via chat interface
2. **WebSocket**: Real-time communication to backend
3. **ReAct Agent**: LangGraph agent processes query using reasoning/action cycles
4. **MCP Tools**: Database queries and visualization generation
5. **Response**: Structured data with visualizations back to frontend

## 🐍 Backend Architecture

### 1. Project Structure Setup

```bash
# Create the backend structure
mkdir -p backend/{models,mcp_servers,tests}
touch backend/{config.py,main.py,langgraph_agent.py,mcp_multi_client.py}
touch backend/{database_operations.py,visualization_operations.py,websocket_manager.py}
```

### 2. Core Configuration (config.py)

**AI Prompt for config.py:**
```
Create a comprehensive configuration module for FastAPI backend with:
- Environment variables for database connection
- OpenAI/Gemini API keys
- MCP server configurations
- WebSocket settings
- Logging configuration
- Use pydantic Settings for validation
- Include development/production modes
```

**Expected Structure:**
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://analytics:password@localhost:5432/analytics_db"
    
    # AI Models
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # MCP Servers
    MCP_CONFIG_PATH: str = "mcp_servers/mcp_config.json"
    
    # WebSocket
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3. FastAPI Main Application (main.py)

**AI Prompt for main.py:**
```
Create FastAPI application with:
- WebSocket endpoint for real-time chat
- CORS middleware for frontend communication
- Health check endpoints
- Proper startup/shutdown event handlers
- Initialize MCP manager and database connections
- Include comprehensive error handling
- Use async patterns throughout
```

**Key Components:**
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

from websocket_manager import WebSocketManager
from mcp_multi_client import mcp_manager
from langgraph_agent import ReActAgent

app = FastAPI(title="MCP UI Analytics API")

# Initialize managers
websocket_manager = WebSocketManager()
react_agent = ReActAgent()

@app.on_event("startup")
async def startup_event():
    await mcp_manager.initialize()
    logger.info("MCP clients initialized")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # WebSocket connection handling
    pass
```

## 🧠 LangGraph ReAct Agent

### 1. ReAct Agent Core Structure (langgraph_agent.py)

**AI Prompt for langgraph_agent.py:**
```
Create a comprehensive LangGraph ReAct agent with:
- StateGraph implementation with ReAct pattern
- System prompt for analytics assistant role
- Database schema awareness for query generation
- Tool selection logic (database vs visualization)
- Error handling and recovery mechanisms
- State management between reasoning/action cycles
- Support for OpenAI GPT-4 and Google Gemini models
- Comprehensive logging and debugging
```

**Agent State Definition:**
```python
from typing import TypedDict, Dict, Any

class ReActAgentState(TypedDict):
    query: str                    # Original user query
    user_id: str                 # User identifier
    reasoning: str               # Agent's reasoning process
    action: str                  # Current action being taken
    observation: str             # Results from actions
    result: Dict[str, Any]       # Final result to return
    error: str                   # Any errors encountered
    step_count: int              # Current step number
    max_steps: int               # Maximum allowed steps
    timestamp: str               # Request timestamp
```

**Core Agent Methods:**
```python
class ReActAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.graph = self._create_graph()
        self.system_prompt = self._create_system_prompt()
    
    async def reason_about_query(self, state: ReActAgentState) -> ReActAgentState:
        """Analyze user query and determine next action."""
        
    async def execute_action(self, state: ReActAgentState) -> ReActAgentState:
        """Execute the determined action using MCP tools."""
        
    async def observe_results(self, state: ReActAgentState) -> ReActAgentState:
        """Process action results and determine if more steps needed."""
        
    async def should_continue(self, state: ReActAgentState) -> str:
        """Determine if agent should continue or finish."""
```

### 2. System Prompt Engineering

**Database Schema Integration:**
```python
def _create_system_prompt(self) -> str:
    return """
You are an intelligent analytics assistant for a data analytics platform.

ROLE: Help business users analyze merchant, user, and redemption data through natural language queries.

DATABASE SCHEMA:
- merchants: id, name, category, description, website_url, logo_url, created_at, updated_at, is_active
- users: id, email, first_name, last_name, phone, date_of_birth, created_at, updated_at, is_active, total_points, tier
- redemptions: id, user_id, merchant_id, amount, points_used, redemption_date, status, transaction_id, notes, created_at
- campaigns: id, name, description, start_date, end_date, is_active, created_at
- user_campaigns: id, user_id, campaign_id, points_earned, participation_date

AVAILABLE TOOLS:
1. db-toolbox:query - Execute SQL queries on the analytics database
2. db-toolbox:get_schema - Get detailed database schema information
3. vizro-mcp:create_dashboard - Create interactive dashboards
4. vizro-mcp:create_chart - Create specific chart visualizations

REACT PATTERN:
1. REASON: Analyze the user's question and determine what data is needed
2. ACT: Use appropriate tools to retrieve data or create visualizations
3. OBSERVE: Review results and determine if more actions are needed
4. Repeat until complete answer is achieved

RESPONSE FORMAT:
- Always provide clear, actionable insights
- Include relevant visualizations for data queries
- Use business-friendly language, not technical jargon
- Highlight key findings and trends
"""
```

### 3. Tool Integration Logic

**AI Prompt for tool integration:**
```
Implement tool selection and execution logic that:
- Determines when to use database queries vs visualizations
- Handles SQL query generation based on natural language
- Manages data transformation for visualization tools
- Implements retry logic for failed tool calls
- Validates tool outputs before proceeding
- Maintains context between multiple tool calls
```

## 🔗 MCP Server Integration

### 1. MCP Client Manager (mcp_multi_client.py)

**AI Prompt for mcp_multi_client.py:**
```
Create a comprehensive MCP client manager that:
- Manages multiple MCP server connections simultaneously
- Loads configuration from JSON files
- Handles connection establishment and maintenance
- Provides unified interface for tool calls
- Implements connection pooling and retry logic
- Handles server failures gracefully
- Includes comprehensive logging and monitoring
- Supports dynamic server addition/removal
```

**Core Manager Structure:**
```python
class MCPClientManager:
    def __init__(self):
        self.clients: Dict[str, ClientSession] = {}
        self.config_path = "mcp_servers/mcp_config.json"
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize all configured MCP clients."""
        
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call on the specified MCP server."""
        
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Get available tools from a specific server."""
        
    async def health_check(self) -> Dict[str, bool]:
        """Check health status of all MCP servers."""
```

### 2. MCP Server Configuration

**Database Toolbox Configuration (mcp_servers/mcp_config.json):**
```json
{
  "mcpServers": {
    "database": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://analytics:password@localhost:5432/analytics_db"
      }
    },
    "vizro": {
      "command": "npx", 
      "args": ["@modelcontextprotocol/server-vizro"],
      "env": {
        "VIZRO_CONFIG_PATH": "./vizro_config.json"
      }
    },
    "code_sandbox": {
      "command": "python",
      "args": ["-m", "mcp.servers.code_sandbox"],
      "env": {
        "SANDBOX_PATH": "/tmp/code_sandbox"
      }
    }
  }
}
```

### 3. Database Operations (database_operations.py)

**AI Prompt for database_operations.py:**
```
Create database operations module that:
- Provides high-level interface for database queries
- Uses MCP database toolbox for query execution
- Includes query validation and sanitization
- Implements connection pooling and retry logic
- Handles schema introspection
- Provides query optimization suggestions
- Includes comprehensive error handling
- Supports both raw SQL and ORM-style queries
```

### 4. Visualization Operations (visualization_operations.py)

**AI Prompt for visualization_operations.py:**
```
Create visualization operations module that:
- Interfaces with Vizro MCP server for chart generation
- Supports multiple chart types (bar, line, pie, scatter, etc.)
- Handles data transformation for visualization
- Provides chart configuration options
- Includes dashboard composition capabilities
- Handles large datasets efficiently
- Provides export capabilities (PNG, SVG, PDF)
- Includes interactive features configuration
```

**Key Methods:**
```python
class VisualizationOperations:
    async def create_dashboard(self, title: str, data: List[Dict[str, Any]], 
                             chart_type: str = "bar") -> Dict[str, Any]:
        """Create interactive dashboard with multiple charts."""
        
    async def create_chart(self, chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create individual chart visualization."""
        
    async def create_table(self, data: List[Dict[str, Any]], 
                          title: str = "Data Table") -> Dict[str, Any]:
        """Create data table visualization."""
```

## 🌐 Frontend Components

### 1. Main Chat Interface (AnalyticsChatbot.tsx)

**AI Prompt for AnalyticsChatbot.tsx:**
```
Create a comprehensive chat interface component with:
- Real-time WebSocket communication
- Message history management
- Typing indicators and loading states
- File upload capabilities for data
- Chart rendering with Vizro configurations
- Responsive design for desktop and mobile
- Accessibility features (ARIA labels, keyboard navigation)
- Error handling and retry mechanisms
- Message threading and conversation context
- Export capabilities for charts and data
```

**Component Structure:**
```typescript
interface AnalyticsChatbotProps {
  userId: string;
  initialQuery?: string;
  onQueryComplete?: (result: QueryResult) => void;
}

const AnalyticsChatbot: React.FC<AnalyticsChatbotProps> = ({
  userId,
  initialQuery,
  onQueryComplete
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  
  const { sendMessage, lastMessage, readyState } = useWebSocket();
  
  // Component implementation
};
```

### 2. WebSocket Hook (useWebSocket.ts)

**AI Prompt for useWebSocket.ts:**
```
Create a robust WebSocket custom hook that:
- Manages WebSocket connection lifecycle
- Handles automatic reconnection with exponential backoff
- Provides connection status monitoring
- Implements message queuing for offline scenarios
- Handles different message types (query, response, error, status)
- Provides TypeScript interfaces for all message types
- Includes heartbeat/ping functionality
- Implements proper cleanup on component unmount
```

### 3. Chart Rendering Component (VizroChart.tsx)

**AI Prompt for VizroChart.tsx:**
```
Create a chart rendering component that:
- Renders Vizro dashboard configurations
- Supports multiple chart types and layouts
- Handles interactive features (zoom, pan, filter)
- Provides export functionality
- Includes loading and error states
- Supports real-time data updates
- Implements responsive design
- Includes accessibility features for charts
- Provides chart customization options
```

## 🗄️ Database Schema

### Schema Definition (scripts/init_db.sql)

**AI Prompt for database schema:**
```
Create a comprehensive PostgreSQL schema for analytics platform with:
- Merchants table with business information
- Users table with customer data and loyalty tiers
- Redemptions table with transaction details
- Campaigns table for marketing campaigns
- User_campaigns table for campaign participation
- Proper foreign key relationships
- Indexes for query optimization
- Sample data generation scripts
- Data validation constraints
- Audit trail columns (created_at, updated_at)
```

**Core Tables:**
```sql
-- Merchants table
CREATE TABLE merchants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Users table with loyalty tiers
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    total_points INTEGER DEFAULT 0,
    tier VARCHAR(20) DEFAULT 'Bronze'
);

-- Redemptions table
CREATE TABLE redemptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    merchant_id INTEGER REFERENCES merchants(id),
    amount DECIMAL(10,2) NOT NULL,
    points_used INTEGER NOT NULL,
    redemption_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed',
    transaction_id VARCHAR(100) UNIQUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Development Workflow

### 1. AI-Assisted Development Pattern

**Step 1: Architecture Planning**
```
Prompt: "Design the overall architecture for [component] that includes:
- Main classes and their responsibilities
- Key methods and their signatures
- Error handling strategy
- Testing approach
- Integration points with other components"
```

**Step 2: TDD Implementation**
```
Prompt: "Write comprehensive tests for [component] that cover:
- Happy path scenarios
- Error conditions and edge cases
- Integration with external services
- Performance requirements
- Mock dependencies appropriately"
```

**Step 3: Implementation**
```
Prompt: "Implement [component] following the designed architecture with:
- Complete type hints and documentation
- Async/await patterns for I/O operations
- Comprehensive error handling
- Logging for debugging and monitoring
- Configuration management"
```

**Step 4: Integration Testing**
```
Prompt: "Create integration tests that verify:
- End-to-end workflows work correctly
- WebSocket communication functions properly
- MCP server integration works as expected
- Database operations complete successfully
- Frontend components render correctly"
```

### 2. Component Development Order

1. **Backend Core (Day 1)**
   - Configuration management
   - Database operations
   - MCP client manager
   - Basic FastAPI application

2. **Agent Implementation (Day 2)**
   - LangGraph ReAct agent
   - Tool integration logic
   - WebSocket manager
   - Visualization operations

3. **Frontend Development (Day 3)**
   - React components
   - WebSocket integration
   - Chart rendering
   - UI/UX polish

4. **Integration & Testing (Day 4)**
   - End-to-end testing
   - Performance optimization
   - Error handling refinement
   - Documentation completion

## 🧪 Testing Strategy

### 1. Backend Testing

**Unit Tests:**
```python
# test_langgraph_agent.py
@pytest.mark.asyncio
async def test_react_agent_query_processing():
    agent = ReActAgent()
    result = await agent.process_query(
        "Show me top merchants by redemption volume",
        "test_user_123"
    )
    assert result["status"] == "success"
    assert "data" in result
    assert "visualization" in result
```

**Integration Tests:**
```python
# test_mcp_integration.py
@pytest.mark.asyncio
async def test_database_mcp_connection():
    await mcp_manager.initialize()
    result = await mcp_manager.call_tool(
        "database", 
        "db-toolbox:query", 
        {"sql": "SELECT COUNT(*) FROM merchants"}
    )
    assert result["success"] is True
```

### 2. Frontend Testing

**Component Tests:**
```typescript
// AnalyticsChatbot.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { AnalyticsChatbot } from './AnalyticsChatbot';

test('sends message when user submits query', async () => {
  render(<AnalyticsChatbot userId="test-user" />);
  
  const input = screen.getByPlaceholderText('Ask a question...');
  const submitButton = screen.getByRole('button', { name: 'Send' });
  
  fireEvent.change(input, { target: { value: 'Show me top merchants' } });
  fireEvent.click(submitButton);
  
  expect(screen.getByText('Show me top merchants')).toBeInTheDocument();
});
```

## 🚀 Deployment Guide

### 1. Docker Configuration

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### 2. Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://analytics:password@db:5432/analytics_db
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: analytics_db
      POSTGRES_USER: analytics
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  postgres_data:
```

## 📚 AI Prompting Best Practices

### 1. Component-Specific Prompts

**For Backend Services:**
```
Create a [service_name] that:
- Follows FastAPI best practices
- Uses async/await for all I/O operations
- Includes comprehensive error handling
- Has complete type hints and documentation
- Implements proper logging
- Includes unit tests with pytest
- Handles edge cases gracefully
```

**For React Components:**
```
Create a React component [component_name] that:
- Uses TypeScript with strict typing
- Implements proper error boundaries
- Follows accessibility guidelines
- Uses custom hooks for reusable logic
- Includes comprehensive prop validation
- Has responsive design
- Includes unit tests with Jest/React Testing Library
```

### 2. Integration Prompts

**For WebSocket Implementation:**
```
Implement WebSocket communication that:
- Handles connection lifecycle properly
- Implements automatic reconnection
- Manages message queuing
- Provides proper error handling
- Includes heartbeat functionality
- Supports message acknowledgments
- Has proper TypeScript interfaces
```

### 3. Testing Prompts

**For Test Generation:**
```
Generate comprehensive tests for [component] that:
- Cover all public methods/functions
- Test both success and failure scenarios
- Include edge cases and boundary conditions
- Mock external dependencies appropriately
- Use proper assertion patterns
- Include performance tests where relevant
- Follow testing best practices
```

## 🎯 Success Criteria

### Technical Implementation
- [ ] Backend serves WebSocket connections successfully
- [ ] ReAct agent processes natural language queries correctly
- [ ] MCP servers integrate and respond to tool calls
- [ ] Database queries execute and return proper results
- [ ] Visualizations generate and render in frontend
- [ ] Real-time communication works end-to-end

### Code Quality
- [ ] All functions have proper type hints and documentation
- [ ] Comprehensive error handling at all levels
- [ ] Test coverage above 80% for critical components
- [ ] Code follows established patterns and conventions
- [ ] Proper logging and monitoring implemented

### User Experience
- [ ] Chat interface is responsive and intuitive
- [ ] Loading states and error messages are clear
- [ ] Visualizations are interactive and informative
- [ ] System handles edge cases gracefully
- [ ] Performance is acceptable for real-time interaction

### Integration
- [ ] All MCP servers connect and function properly
- [ ] Database schema supports required queries
- [ ] Frontend components integrate seamlessly
- [ ] Deployment pipeline works correctly
- [ ] Documentation is complete and accurate

This guide provides the foundation for systematically building the RewardOps Analytics POC using AI development tools. Follow the patterns and prompts provided to ensure consistent, high-quality implementation across all components.
