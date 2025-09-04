# Development Patterns and Standards

This document defines the coding patterns, architectural principles, and development standards for the RewardOps Analytics POC project.

## 🏗️ Architectural Principles

### 1. Separation of Concerns
- **Backend**: API logic, business rules, data processing
- **Frontend**: UI components, user interaction, state management
- **Database**: Data storage, relationships, constraints
- **MCP Servers**: External tool integration, specialized functionality

### 2. Async-First Design
- All I/O operations use async/await patterns
- WebSocket communication is non-blocking
- Database queries are asynchronous
- MCP tool calls are async

### 3. Error-First Approach
- Comprehensive error handling at all layers
- Graceful degradation for service failures
- User-friendly error messages
- Detailed logging for debugging

### 4. Test-Driven Development
- Write tests before implementation
- Maintain high test coverage
- Test both success and failure scenarios
- Integration tests for critical paths

## 🐍 Python Backend Patterns

### 1. Type Hints and Documentation

```python
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    """WebSocket message types."""
    QUERY = "QUERY"
    RESPONSE = "RESPONSE"
    ERROR = "ERROR"
    STATUS_UPDATE = "STATUS_UPDATE"

@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    payload: Dict[str, Any]
    timestamp: str
    message_id: str

async def process_analytics_query(
    query: str,
    user_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a natural language analytics query.
    
    This function takes a user's natural language query and processes it
    through the ReAct agent to generate a response with data and visualizations.
    
    Args:
        query: The natural language query from the user
        user_id: Unique identifier for the user making the query
        context: Optional context data for the query
        
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - data: Query results if successful
        - visualization: Vizro configuration if applicable
        - error: Error message if failed
        
    Raises:
        QueryProcessingError: If the query cannot be processed
        DatabaseError: If database operations fail
        VisualizationError: If visualization generation fails
        
    Example:
        >>> result = await process_analytics_query(
        ...     "Show me top merchants by redemption volume",
        ...     "user123"
        ... )
        >>> print(result["status"])
        "success"
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Error processing query '{query}': {e}")
        raise QueryProcessingError(f"Failed to process query: {e}")
```

### 2. Error Handling Patterns

```python
from fastapi import HTTPException
from pydantic import ValidationError

class AnalyticsError(Exception):
    """Base exception for analytics operations."""
    pass

class QueryProcessingError(AnalyticsError):
    """Raised when query processing fails."""
    pass

class DatabaseError(AnalyticsError):
    """Raised when database operations fail."""
    pass

class VisualizationError(AnalyticsError):
    """Raised when visualization generation fails."""
    pass

async def safe_database_query(query: str) -> List[Dict[str, Any]]:
    """Execute database query with comprehensive error handling."""
    try:
        result = await mcp_client.call_tool("db-toolbox:query", {"query": query})
        return result.get("data", [])
    except ValidationError as e:
        logger.error(f"Query validation failed: {e}")
        raise QueryProcessingError(f"Invalid query format: {e}")
    except ConnectionError as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseError(f"Database unavailable: {e}")
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        raise DatabaseError(f"Database operation failed: {e}")
```

### 3. Configuration Management

```python
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    
    # Application
    log_level: str = Field("INFO", env="LOG_LEVEL")
    debug: bool = Field(False, env="DEBUG")
    
    # MCP Servers
    mcp_database_config: str = Field("mcp_servers/database_config.json")
    mcp_vizro_config: str = Field("mcp_servers/vizro_config.json")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

### 4. Logging Patterns

```python
import logging
import json
from datetime import datetime
from typing import Any, Dict

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_analytics_event(
    event_type: str,
    user_id: str,
    data: Dict[str, Any],
    success: bool = True
) -> None:
    """Log analytics events with structured data."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "success": success,
        "data": data
    }
    
    if success:
        logger.info(f"Analytics event: {json.dumps(log_data)}")
    else:
        logger.error(f"Analytics event failed: {json.dumps(log_data)}")
```

## ⚛️ React Frontend Patterns

### 1. Component Structure

```typescript
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Message, WebSocketStatus } from '../types/api';

interface AnalyticsChatbotProps {
  userId: string;
  onMessageSent?: (message: string) => void;
  className?: string;
}

const AnalyticsChatbot: React.FC<AnalyticsChatbotProps> = ({
  userId,
  onMessageSent,
  className = ''
}) => {
  // State management
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<WebSocketStatus>('connecting');
  
  // Memoized values
  const canSendMessage = useMemo(() => {
    return inputValue.trim().length > 0 && 
           connectionStatus === 'connected' && 
           !isLoading;
  }, [inputValue, connectionStatus, isLoading]);
  
  // Event handlers
  const handleSendMessage = useCallback(async () => {
    if (!canSendMessage) return;
    
    const message = inputValue.trim();
    setInputValue('');
    setIsLoading(true);
    
    try {
      await sendMessage(message);
      onMessageSent?.(message);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Handle error appropriately
    } finally {
      setIsLoading(false);
    }
  }, [canSendMessage, inputValue, onMessageSent]);
  
  // Effects
  useEffect(() => {
    // WebSocket connection logic
  }, [userId]);
  
  return (
    <div className={`analytics-chatbot ${className}`}>
      {/* Component JSX */}
    </div>
  );
};

export default AnalyticsChatbot;
```

### 2. Custom Hooks

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketMessage, Message } from '../types/api';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = ({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  reconnectInterval = 5000,
  maxReconnectAttempts = 5
}: UseWebSocketOptions) => {
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error' | 'disconnected'>('connecting');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      
      ws.onopen = () => {
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        onOpen?.();
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        setConnectionStatus('error');
        onError?.(error);
      };
      
      ws.onclose = () => {
        setConnectionStatus('disconnected');
        onClose?.();
        
        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            setConnectionStatus('connecting');
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [url, onMessage, onError, onOpen, onClose, reconnectInterval, maxReconnectAttempts]);
  
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }, []);
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
  }, []);
  
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);
  
  return {
    connectionStatus,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect
  };
};
```

### 3. State Management Patterns

```typescript
import { createContext, useContext, useReducer, ReactNode } from 'react';

// Types
interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  connectionStatus: WebSocketStatus;
}

type ChatAction =
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CONNECTION_STATUS'; payload: WebSocketStatus }
  | { type: 'CLEAR_MESSAGES' };

// Reducer
const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
        error: null
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };
    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        connectionStatus: action.payload
      };
    case 'CLEAR_MESSAGES':
      return {
        ...state,
        messages: []
      };
    default:
      return state;
  }
};

// Context
const ChatContext = createContext<{
  state: ChatState;
  dispatch: React.Dispatch<ChatAction>;
} | null>(null);

// Provider
export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, {
    messages: [],
    isLoading: false,
    error: null,
    connectionStatus: 'connecting'
  });
  
  return (
    <ChatContext.Provider value={{ state, dispatch }}>
      {children}
    </ChatContext.Provider>
  );
};

// Hook
export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
```

## 🗄️ Database Patterns

### 1. Query Patterns

```python
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

class DatabaseManager:
    """Database operations manager with error handling."""
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query with proper error handling.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of result dictionaries
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(text(query), params or {})
                return [dict(row._mapping) for row in result.fetchall()]
        except SQLAlchemyError as e:
            logger.error(f"Database query failed: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
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
            SUM(r.amount) as total_volume,
            AVG(r.amount) as avg_redemption_value
        FROM merchants m
        LEFT JOIN redemptions r ON m.id = r.merchant_id
        WHERE m.is_active = true
        """
        
        params = {}
        if start_date:
            query += " AND r.redemption_date >= :start_date"
            params["start_date"] = start_date
        if end_date:
            query += " AND r.redemption_date <= :end_date"
            params["end_date"] = end_date
            
        query += """
        GROUP BY m.id, m.name, m.category
        ORDER BY total_volume DESC NULLS LAST
        LIMIT :limit
        """
        params["limit"] = limit
        
        return await self.execute_query(query, params)
```

### 2. Data Validation Patterns

```python
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime

class Merchant(BaseModel):
    """Merchant data model with validation."""
    id: int
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Website URL must start with http:// or https://')
        return v
    
    @validator('logo_url')
    def validate_logo_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Logo URL must start with http:// or https://')
        return v

class Redemption(BaseModel):
    """Redemption data model with validation."""
    id: int
    user_id: int
    merchant_id: int
    amount: float = Field(..., gt=0)
    points_used: int = Field(..., gt=0)
    redemption_date: datetime
    status: str = Field(..., regex='^(completed|pending|cancelled)$')
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2)
```

## 🧪 Testing Patterns

### 1. Backend Testing

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import asyncio

@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    client = AsyncMock()
    client.call_tool.return_value = {
        "data": [
            {"id": 1, "name": "Test Merchant", "volume": 1000}
        ]
    }
    return client

@pytest.fixture
def sample_query_result():
    """Sample query result for testing."""
    return [
        {
            "id": 1,
            "name": "Test Merchant",
            "category": "Retail",
            "redemption_count": 50,
            "total_volume": 10000.00,
            "avg_redemption_value": 200.00
        }
    ]

@pytest.mark.asyncio
async def test_process_analytics_query_success(mock_mcp_client, sample_query_result):
    """Test successful analytics query processing."""
    with patch('app.mcp_client', mock_mcp_client):
        result = await process_analytics_query(
            "Show me top merchants by redemption volume",
            "user123"
        )
        
        assert result["status"] == "success"
        assert "data" in result
        assert "visualization" in result
        mock_mcp_client.call_tool.assert_called()

@pytest.mark.asyncio
async def test_process_analytics_query_database_error(mock_mcp_client):
    """Test analytics query processing with database error."""
    mock_mcp_client.call_tool.side_effect = DatabaseError("Connection failed")
    
    with patch('app.mcp_client', mock_mcp_client):
        with pytest.raises(QueryProcessingError):
            await process_analytics_query(
                "Show me top merchants",
                "user123"
            )

def test_websocket_connection():
    """Test WebSocket connection establishment."""
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Test connection
        data = websocket.receive_json()
        assert data["type"] == "STATUS_UPDATE"
        assert data["payload"]["status"] == "connected"
```

### 2. Frontend Testing

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AnalyticsChatbot } from '../AnalyticsChatbot';
import { ChatProvider } from '../contexts/ChatContext';

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  readyState: WebSocket.OPEN
};

// Mock the WebSocket constructor
global.WebSocket = jest.fn(() => mockWebSocket) as any;

describe('AnalyticsChatbot', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render chat interface', () => {
    render(
      <ChatProvider>
        <AnalyticsChatbot userId="user123" />
      </ChatProvider>
    );
    
    expect(screen.getByPlaceholderText('Ask about your data...')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  it('should send message when form is submitted', async () => {
    render(
      <ChatProvider>
        <AnalyticsChatbot userId="user123" />
      </ChatProvider>
    );
    
    const input = screen.getByPlaceholderText('Ask about your data...');
    const button = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Show me top merchants' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'QUERY',
          payload: {
            query: 'Show me top merchants',
            userId: 'user123'
          }
        })
      );
    });
  });

  it('should display received messages', async () => {
    render(
      <ChatProvider>
        <AnalyticsChatbot userId="user123" />
      </ChatProvider>
    );
    
    // Simulate receiving a message
    const message = {
      type: 'RESPONSE',
      payload: {
        result: { data: [] },
        visualization: { title: 'Test Chart' }
      }
    };
    
    // Trigger WebSocket message event
    const event = new MessageEvent('message', {
      data: JSON.stringify(message)
    });
    
    mockWebSocket.onmessage(event);
    
    await waitFor(() => {
      expect(screen.getByText('Test Chart')).toBeInTheDocument();
    });
  });
});
```

## 🔧 Configuration Patterns

### 1. Environment Configuration

```python
# config.py
import os
from pathlib import Path
from typing import Optional

class Config:
    """Application configuration with environment variable support."""
    
    # Base configuration
    BASE_DIR = Path(__file__).parent.parent
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # API configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # MCP configuration
    MCP_DATABASE_CONFIG = os.getenv('MCP_DATABASE_CONFIG', 'mcp_servers/database_config.json')
    MCP_VIZRO_CONFIG = os.getenv('MCP_VIZRO_CONFIG', 'mcp_servers/vizro_config.json')
    
    # WebSocket configuration
    WS_HEARTBEAT_INTERVAL = int(os.getenv('WS_HEARTBEAT_INTERVAL', '30'))
    WS_MAX_CONNECTIONS = int(os.getenv('WS_MAX_CONNECTIONS', '100'))
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        required_vars = ['DATABASE_URL']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
```

### 2. MCP Configuration

```json
{
  "mcpServers": {
    "database": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://rewardops:password@localhost:5432/rewardops_db"
      }
    },
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

## 📊 Performance Patterns

### 1. Caching Patterns

```python
import redis
import json
from typing import Any, Optional
from functools import wraps

redis_client = redis.from_url(settings.REDIS_URL)

def cache_result(expiry: int = 300):
    """Cache function results in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiry, json.dumps(result))
            
            return result
        return wrapper
    return decorator

@cache_result(expiry=600)  # Cache for 10 minutes
async def get_merchants_by_redemption_volume(limit: int = 10) -> List[Dict[str, Any]]:
    """Get merchants by redemption volume with caching."""
    # Implementation here
    pass
```

### 2. Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@asynccontextmanager
async def get_db_session():
    """Get database session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## 🔒 Security Patterns

### 1. Input Validation

```python
from pydantic import BaseModel, validator
import re

class QueryRequest(BaseModel):
    """Query request with validation."""
    query: str
    user_id: str
    
    @validator('query')
    def validate_query(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Query must be at least 3 characters long')
        if len(v) > 1000:
            raise ValueError('Query must be less than 1000 characters')
        
        # Check for potentially malicious patterns
        dangerous_patterns = [
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r';\s*--',
            r'union\s+select'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v.lower()):
                raise ValueError('Query contains potentially dangerous SQL patterns')
        
        return v.strip()
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('User ID contains invalid characters')
        return v
```

### 2. Rate Limiting

```python
from fastapi import Request, HTTPException
import time
from collections import defaultdict

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is within rate limits."""
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests outside the window
        user_requests[:] = [
            req_time for req_time in user_requests 
            if now - req_time < self.window_seconds
        ]
        
        # Check if under limit
        if len(user_requests) >= self.max_requests:
            return False
        
        # Add current request
        user_requests.append(now)
        return True

rate_limiter = RateLimiter(max_requests=50, window_seconds=3600)

async def check_rate_limit(request: Request, user_id: str):
    """Check rate limit for user."""
    if not rate_limiter.is_allowed(user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
```

These patterns provide a solid foundation for building maintainable, scalable, and secure applications. Follow these patterns consistently throughout the project to ensure code quality and team productivity.
