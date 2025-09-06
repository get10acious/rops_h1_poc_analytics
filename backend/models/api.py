"""
API models and data structures for MCP UI Chat Analytics POC.

This module defines all the Pydantic models used for API requests, responses,
and WebSocket communication.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class MessageType(str, Enum):
    """WebSocket message types."""
    QUERY = "QUERY"
    USER_QUERY = "user_query"  # Frontend compatibility
    RESPONSE = "RESPONSE"
    ERROR = "ERROR"
    STATUS_UPDATE = "STATUS_UPDATE"
    PING = "PING"
    PONG = "PONG"

class WebSocketStatus(str, Enum):
    """WebSocket connection status."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class ChartType(str, Enum):
    """Supported chart types."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"

# Base WebSocket Message
class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""
    type: MessageType
    payload: Optional[Dict[str, Any]] = None
    content: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    message_id: Optional[str] = None

# Specific Message Types
class QueryMessage(WebSocketMessage):
    """Query message from client."""
    type: MessageType = MessageType.QUERY
    payload: Dict[str, Any] = Field(..., description="Query payload containing query and user_id")

class ResponseMessage(WebSocketMessage):
    """Response message to client."""
    type: MessageType = MessageType.RESPONSE
    payload: Dict[str, Any] = Field(..., description="Response payload containing result and visualization")

class ErrorMessage(WebSocketMessage):
    """Error message to client."""
    type: MessageType = MessageType.ERROR
    payload: Dict[str, Any] = Field(..., description="Error payload containing error details")

class StatusUpdateMessage(WebSocketMessage):
    """Status update message to client."""
    type: MessageType = MessageType.STATUS_UPDATE
    payload: Dict[str, Any] = Field(..., description="Status payload containing status information")

# Data Models
class Merchant(BaseModel):
    """Merchant data model."""
    id: int
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class User(BaseModel):
    """User data model."""
    id: int
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    total_points: int = Field(0, ge=0)
    tier: str = Field("bronze", pattern=r'^(bronze|silver|gold|platinum)$')

class Redemption(BaseModel):
    """Redemption data model."""
    id: int
    user_id: int
    merchant_id: int
    amount: float = Field(..., gt=0)
    points_used: int = Field(..., gt=0)
    redemption_date: datetime
    status: str = Field(..., pattern=r'^(completed|pending|cancelled)$')
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

class Campaign(BaseModel):
    """Campaign data model."""
    id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

# Analytics Models
class AnalyticsQuery(BaseModel):
    """Analytics query request model."""
    query: str = Field(..., min_length=3, max_length=1000)
    user_id: str = Field(..., min_length=1, max_length=100)
    context: Optional[Dict[str, Any]] = None
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class AnalyticsResult(BaseModel):
    """Analytics query result model."""
    status: str = Field(..., pattern=r'^(success|error)$')
    data: List[Dict[str, Any]] = Field(default_factory=list)
    visualization: Optional[Dict[str, Any]] = None
    query: str
    query_id: str
    processing_time: float = Field(..., ge=0)
    timestamp: datetime
    error: Optional[str] = None

class VizroConfig(BaseModel):
    """Vizro visualization configuration."""
    title: str = Field(..., min_length=1, max_length=255)
    chart_type: ChartType = ChartType.BAR
    data: List[Dict[str, Any]] = Field(..., min_length=1)
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    width: int = Field(800, ge=200, le=2000)
    height: int = Field(600, ge=200, le=2000)
    theme: str = Field("default", pattern=r'^(default|dark|light)$')
    
    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        if not v:
            raise ValueError('Data cannot be empty')
        return v

class UIResource(BaseModel):
    """MCP UI Resource for dynamic UI generation."""
    uri: str = Field(..., description="Unique resource identifier")
    mime_type: str = Field("text/html", description="MIME type of the resource")
    text: str = Field(..., description="Resource content")
    encoding: str = Field("text", description="Content encoding")

# API Request/Response Models
class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str
    mcp_servers: Optional[Dict[str, Any]] = None

class StatusResponse(BaseModel):
    """System status response model."""
    status: str
    mcp_servers: Dict[str, Any]
    websocket_connections: int
    timestamp: str

class TestQueryRequest(BaseModel):
    """Test query request model."""
    query: str = Field(..., min_length=3, max_length=1000)
    user_id: str = Field("test_user", max_length=100)

class TestQueryResponse(BaseModel):
    """Test query response model."""
    status: str
    result: Dict[str, Any]
    timestamp: str

# Error Models
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: str
    request_id: Optional[str] = None

class ValidationError(BaseModel):
    """Validation error model."""
    field: str
    message: str
    value: Any

# WebSocket Connection Models
class ConnectionInfo(BaseModel):
    """WebSocket connection information."""
    client_id: str
    connected_at: datetime
    last_activity: datetime
    user_id: Optional[str] = None
    status: WebSocketStatus

class ConnectionStats(BaseModel):
    """WebSocket connection statistics."""
    total_connections: int
    active_connections: int
    total_messages: int
    average_response_time: float

# MCP Tool Models
class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class MCPToolCall(BaseModel):
    """MCP tool call request."""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None

class MCPToolResult(BaseModel):
    """MCP tool call result."""
    tool_name: str
    result: Dict[str, Any]
    call_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

# Agent Models
class AgentState(BaseModel):
    """ReAct agent state."""
    query: str
    reasoning: Optional[str] = None
    action: Optional[str] = None
    observation: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    step_count: int = 0
    max_steps: int = 10

class AgentStep(BaseModel):
    """Single agent step."""
    step_type: str = Field(..., pattern=r'^(reason|act|observe)$')
    content: str
    timestamp: datetime
    step_number: int

class AgentExecution(BaseModel):
    """Complete agent execution."""
    query: str
    user_id: str
    steps: List[AgentStep]
    final_result: Optional[Dict[str, Any]] = None
    success: bool
    execution_time: float
    timestamp: datetime

# Database Query Models
class SQLQuery(BaseModel):
    """SQL query model."""
    query: str
    parameters: Optional[Dict[str, Any]] = None
    timeout: int = Field(30, ge=1, le=300)

class QueryResult(BaseModel):
    """Database query result."""
    data: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    columns: List[str]

# Rate Limiting Models
class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    user_id: str
    requests_made: int
    requests_allowed: int
    window_start: datetime
    window_end: datetime
    reset_time: datetime

class RateLimitResponse(BaseModel):
    """Rate limit response."""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None

# Export all models
__all__ = [
    "MessageType",
    "WebSocketStatus", 
    "ChartType",
    "WebSocketMessage",
    "QueryMessage",
    "ResponseMessage",
    "ErrorMessage",
    "StatusUpdateMessage",
    "Merchant",
    "User",
    "Redemption",
    "Campaign",
    "AnalyticsQuery",
    "AnalyticsResult",
    "UIConfig",
    "UIResource",
    "HealthCheckResponse",
    "StatusResponse",
    "TestQueryRequest",
    "TestQueryResponse",
    "ErrorResponse",
    "ValidationError",
    "ConnectionInfo",
    "ConnectionStats",
    "MCPTool",
    "MCPToolCall",
    "MCPToolResult",
    "AgentState",
    "AgentStep",
    "AgentExecution",
    "SQLQuery",
    "QueryResult",
    "RateLimitInfo",
    "RateLimitResponse"
]
