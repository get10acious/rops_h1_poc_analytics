# AI Assistant Guide for RewardOps Analytics POC

This guide provides comprehensive instructions for AI coding assistants to help students build the RewardOps Natural Language Analytics POC. Follow these patterns and rules to ensure consistent, high-quality development.

## 🎯 System Overview

### Business Context
- **Company**: RewardOps - A rewards and loyalty platform
- **Domain**: Merchant rewards, user redemptions, campaign management
- **Goal**: Transform static admin homepage into intelligent analytics dashboard
- **Users**: Non-technical business users who need data insights

### Technical Architecture
- **Backend**: FastAPI with WebSocket support
- **Frontend**: React/Next.js with real-time chat interface
- **Database**: PostgreSQL with sample RewardOps data
- **AI Agent**: LangGraph-based ReAct agent
- **MCP Integration**: Database Toolbox + Vizro MCP servers
- **Communication**: WebSocket for real-time chat

## 📋 Development Rules and Patterns

### 1. Code Quality Standards

#### Python Backend
- **Type Hints**: All functions must include complete type hints
- **Async/Await**: Use async patterns for all I/O operations
- **Error Handling**: Comprehensive try-catch blocks with logging
- **Documentation**: Docstrings for all functions and classes
- **Testing**: TDD approach - write tests first

```python
# Example pattern
async def process_analytics_query(
    query: str, 
    user_id: str
) -> Dict[str, Any]:
    """
    Process a natural language analytics query.
    
    Args:
        query: Natural language query from user
        user_id: ID of the user making the query
        
    Returns:
        Dictionary containing query results and metadata
        
    Raises:
        QueryProcessingError: If query cannot be processed
        DatabaseError: If database operation fails
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise
```

#### React Frontend
- **Functional Components**: Use React hooks, no class components
- **TypeScript**: Strict type checking enabled
- **Custom Hooks**: Extract reusable logic into custom hooks
- **Error Boundaries**: Implement error handling for components
- **Accessibility**: Follow WCAG guidelines

```typescript
// Example pattern
interface AnalyticsChatbotProps {
  userId: string;
  onMessageSent: (message: string) => void;
}

const AnalyticsChatbot: React.FC<AnalyticsChatbotProps> = ({
  userId,
  onMessageSent
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  
  // Implementation here
};
```

### 2. AI Assistant Interaction Patterns

#### Context Setting
Always start with comprehensive context:

```
@agent We are building a RewardOps analytics POC. Here's the context:

BUSINESS DOMAIN:
- RewardOps is a loyalty platform with merchants, users, and redemptions
- Business users need to query data like "top merchants by redemption volume"
- System should generate interactive charts and dashboards

TECHNICAL STACK:
- Backend: FastAPI + WebSocket + LangGraph + MCP
- Frontend: React + Next.js + TypeScript
- Database: PostgreSQL with merchants, users, redemptions tables
- MCP Servers: Database Toolbox, Vizro MCP

CURRENT STATE:
- [Describe what's already implemented]
- [Describe what needs to be built next]

CODING STANDARDS:
- Python: Type hints, async/await, comprehensive error handling
- React: Functional components, TypeScript, custom hooks
- Testing: TDD approach, write tests first

Please help me implement [specific feature] following these patterns.
```

#### Progressive Implementation
Follow the TDD cycle:
1. **Red**: Write failing tests
2. **Green**: Write minimal code to pass tests
3. **Refactor**: Improve code while keeping tests green

#### Validation Requests
Always ask for validation at key points:
- After implementing core functionality
- Before integrating components
- After completing major features

### 3. Database Schema Context

#### Core Tables
```sql
-- Merchants table
CREATE TABLE merchants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Redemptions table
CREATE TABLE redemptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    merchant_id INTEGER REFERENCES merchants(id),
    amount DECIMAL(10,2),
    points_used INTEGER,
    redemption_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'completed'
);
```

#### Sample Queries
Common business questions students should be able to answer:
- "Show me the top 10 merchants by redemption volume"
- "What are the most popular redemption categories?"
- "How many users redeemed rewards this month?"
- "Which merchants have the highest average redemption value?"

### 4. MCP Integration Patterns

#### Database Toolbox MCP
```python
# Example usage pattern
async def query_database(query: str) -> List[Dict[str, Any]]:
    """Execute SQL query using MCP Database Toolbox."""
    try:
        result = await mcp_client.call_tool(
            "db-toolbox:query",
            {"query": query}
        )
        return result.get("data", [])
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise DatabaseError(f"Query execution failed: {e}")
```

#### Vizro MCP
```python
# Example usage pattern
async def create_visualization(
    data: List[Dict[str, Any]], 
    chart_type: str,
    title: str
) -> Dict[str, Any]:
    """Create visualization using Vizro MCP."""
    try:
        vizro_config = {
            "title": title,
            "chart_type": chart_type,
            "data": data
        }
        result = await mcp_client.call_tool(
            "vizro-mcp:create_dashboard",
            vizro_config
        )
        return result
    except Exception as e:
        logger.error(f"Visualization creation failed: {e}")
        raise VisualizationError(f"Chart generation failed: {e}")
```

### 5. WebSocket Communication Protocol

#### Message Types
```typescript
interface WebSocketMessage {
  type: 'QUERY' | 'RESPONSE' | 'ERROR' | 'STATUS_UPDATE';
  payload: any;
  timestamp: string;
  messageId: string;
}

interface QueryMessage extends WebSocketMessage {
  type: 'QUERY';
  payload: {
    query: string;
    userId: string;
  };
}

interface ResponseMessage extends WebSocketMessage {
  type: 'RESPONSE';
  payload: {
    result: any;
    visualization?: VizroConfig;
    queryId: string;
  };
}
```

#### Error Handling
```typescript
// Frontend error handling pattern
const handleWebSocketError = (error: Event) => {
  console.error('WebSocket error:', error);
  setConnectionStatus('error');
  // Implement reconnection logic
  setTimeout(() => {
    reconnectWebSocket();
  }, 5000);
};
```

### 6. LangGraph Agent Patterns

#### ReAct Agent Structure
```python
from langgraph import StateGraph, END
from typing import TypedDict, List

class AgentState(TypedDict):
    query: str
    reasoning: str
    action: str
    observation: str
    result: dict
    error: str

def create_react_agent():
    """Create ReAct agent for query processing."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("reason", reason_about_query)
    workflow.add_node("act", execute_action)
    workflow.add_node("observe", observe_result)
    
    # Add edges
    workflow.add_edge("reason", "act")
    workflow.add_edge("act", "observe")
    workflow.add_edge("observe", END)
    
    return workflow.compile()
```

### 7. Testing Patterns

#### Backend Testing
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    client = AsyncMock()
    client.call_tool.return_value = {"data": []}
    return client

@pytest.mark.asyncio
async def test_process_analytics_query(mock_mcp_client):
    """Test analytics query processing."""
    with patch('app.mcp_client', mock_mcp_client):
        result = await process_analytics_query(
            "Show me top merchants",
            "user123"
        )
        assert result["status"] == "success"
        mock_mcp_client.call_tool.assert_called_once()
```

#### Frontend Testing
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AnalyticsChatbot } from '../AnalyticsChatbot';

describe('AnalyticsChatbot', () => {
  it('should send message when form is submitted', async () => {
    const mockOnMessageSent = jest.fn();
    render(<AnalyticsChatbot userId="user123" onMessageSent={mockOnMessageSent} />);
    
    const input = screen.getByPlaceholderText('Ask about your data...');
    const button = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Show me top merchants' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockOnMessageSent).toHaveBeenCalledWith('Show me top merchants');
    });
  });
});
```

## 🚀 Implementation Phases

### Phase 1: Foundation Setup
1. **Environment Setup**: Docker, dependencies, MCP configuration
2. **Database Initialization**: Schema, sample data, connection
3. **Basic WebSocket**: Connection, message handling, error handling
4. **Frontend Skeleton**: Chat interface, message display, input handling

### Phase 2: Core Functionality
1. **MCP Integration**: Database Toolbox, Vizro MCP setup
2. **LangGraph Agent**: ReAct pattern implementation
3. **Query Processing**: Natural language to SQL translation
4. **Visualization**: Chart generation and display

### Phase 3: Enhancement
1. **Error Handling**: Comprehensive error management
2. **Performance**: Optimization, caching, connection pooling
3. **Testing**: Unit tests, integration tests, E2E tests
4. **Documentation**: API docs, user guides, deployment guides

## 🔧 Common Implementation Tasks

### 1. Setting Up MCP Clients
```python
# Pattern for MCP client setup
async def setup_mcp_clients():
    """Initialize and configure MCP clients."""
    clients = {}
    
    # Database Toolbox
    clients['database'] = await create_mcp_client(
        server_name="db-toolbox",
        config_path="mcp_servers/database_config.json"
    )
    
    # Vizro MCP
    clients['vizro'] = await create_mcp_client(
        server_name="vizro-mcp",
        config_path="mcp_servers/vizro_config.json"
    )
    
    return clients
```

### 2. WebSocket Message Handling
```python
# Pattern for WebSocket message processing
async def handle_websocket_message(websocket, message: dict):
    """Process incoming WebSocket messages."""
    try:
        message_type = message.get("type")
        
        if message_type == "QUERY":
            await process_user_query(websocket, message["payload"])
        elif message_type == "PING":
            await websocket.send_json({"type": "PONG"})
        else:
            await send_error(websocket, f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await send_error(websocket, "Internal server error")
```

### 3. Frontend State Management
```typescript
// Pattern for chat state management
const useChatState = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  
  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
  }, []);
  
  const sendMessage = useCallback(async (content: string) => {
    const message: Message = {
      id: generateId(),
      content,
      type: 'user',
      timestamp: new Date().toISOString()
    };
    
    addMessage(message);
    setIsLoading(true);
    
    try {
      await websocket.send(JSON.stringify({
        type: 'QUERY',
        payload: { query: content, userId: 'current_user' }
      }));
    } catch (error) {
      console.error('Failed to send message:', error);
      addMessage({
        id: generateId(),
        content: 'Failed to send message. Please try again.',
        type: 'error',
        timestamp: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
    }
  }, [addMessage, websocket]);
  
  return {
    messages,
    isLoading,
    connectionStatus,
    sendMessage,
    addMessage
  };
};
```

## 🎯 Success Criteria

### Functional Requirements
- [ ] Users can ask natural language questions
- [ ] System translates queries to SQL
- [ ] Database queries return correct results
- [ ] Visualizations are generated and displayed
- [ ] Real-time communication works reliably
- [ ] Error handling provides helpful feedback

### Technical Requirements
- [ ] All code includes proper type hints
- [ ] Tests cover core functionality
- [ ] WebSocket connection is stable
- [ ] MCP integration works correctly
- [ ] Performance is acceptable (< 3s response time)
- [ ] Code follows established patterns

### Quality Requirements
- [ ] Code is well-documented
- [ ] Error messages are user-friendly
- [ ] UI is responsive and accessible
- [ ] System handles edge cases gracefully
- [ ] Deployment process is documented

## 🆘 Troubleshooting Guide

### Common Issues

#### 1. MCP Connection Failures
```bash
# Check MCP server status
make test-mcp

# Verify configuration
cat backend/mcp_servers/mcp_config.json

# Check logs
make logs-backend
```

#### 2. WebSocket Connection Issues
```typescript
// Debug WebSocket connection
const debugWebSocket = () => {
  websocket.onopen = () => console.log('WebSocket connected');
  websocket.onclose = () => console.log('WebSocket disconnected');
  websocket.onerror = (error) => console.error('WebSocket error:', error);
};
```

#### 3. Database Connection Problems
```bash
# Test database connection
make check-db

# Check database logs
make docker-logs

# Reset database
make docker-down && make docker-up && make init-db
```

## 📚 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/)
- [React WebSocket Hooks](https://github.com/robtaussig/react-use-websocket)
- [Vizro Documentation](https://vizro.mckinsey.com/)

Remember: The goal is to help students build a working POC in one day. Focus on clear, actionable guidance and maintain high code quality standards throughout the development process.
