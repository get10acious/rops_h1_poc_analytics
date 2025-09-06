"""
MCP UI Chat Analytics POC - FastAPI Backend

This is the main FastAPI application that serves as the MCP Host & Orchestrator
for the natural language analytics system.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from mcp_multi_client import mcp_manager
from langgraph_agent import LangGraphReActAgent
from websocket_manager import WebSocketManager
from config import settings
from models.api import (
    WebSocketMessage, 
    QueryMessage, 
    ResponseMessage, 
    ErrorMessage,
    StatusUpdateMessage
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global WebSocket manager
websocket_manager = WebSocketManager()

# Global ReAct agent
react_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting MCP UI Chat Analytics POC Backend...")
    
    try:
        # Initialize MCP clients
        await mcp_manager.initialize()
        logger.info("MCP clients initialized successfully")
        
        # Initialize ReAct agent
        global react_agent
        react_agent = LangGraphReActAgent()
        await react_agent.initialize()
        logger.info("ReAct agent initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down MCP UI Chat Analytics POC Backend...")
        await mcp_manager.close_all()
        logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="MCP UI Chat Analytics POC",
    description="Natural Language Analytics API with MCP Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time analytics chat."""
    await websocket_manager.connect(websocket)
    
    try:
        # Send initial status update
        status_message = StatusUpdateMessage(
            type="STATUS_UPDATE",
            payload={"status": "connected", "message": "Connected to analytics service"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            message_id=f"status_{datetime.now(timezone.utc).timestamp()}"
        )
        await websocket_manager.send_personal_message(status_message.model_dump(), websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                
                # Handle flexible message format from frontend
                if "type" in message_data and message_data["type"] in ["user_query", "QUERY", "USER_QUERY"]:
                    # Create a properly formatted WebSocket message
                    # Check if payload already exists (new format) or use content (old format)
                    if "payload" in message_data:
                        payload = message_data["payload"]
                    elif "content" in message_data:
                        # content is an object with query and session_id
                        payload = message_data["content"]
                    else:
                        payload = {"query": message_data.get("query", "")}
                    
                    formatted_message = {
                        "type": "QUERY",  # Standardize to QUERY
                        "payload": payload,
                        "timestamp": message_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "message_id": message_data.get("message_id", f"msg_{datetime.now().timestamp()}")
                    }
                    message = WebSocketMessage(**formatted_message)
                else:
                    # Try to parse as standard WebSocket message
                    message = WebSocketMessage(**message_data)
                
                logger.info(f"Received message: {message.type} from {websocket.client}")
                logger.debug(f"Message payload: {message.payload}")
                
                # Handle different message types
                if message.type in ["QUERY", "user_query", "USER_QUERY"]:
                    await handle_analytics_query(message, websocket)
                elif message.type == "PING":
                    # Respond to ping with pong
                    pong_message = StatusUpdateMessage(
                        type="STATUS_UPDATE",
                        payload={"status": "pong", "timestamp": datetime.now(timezone.utc).isoformat()},
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        message_id=f"pong_{datetime.now(timezone.utc).timestamp()}"
                    )
                    await websocket_manager.send_personal_message(pong_message.model_dump(), websocket)
                else:
                    # Unknown message type
                    error_message = ErrorMessage(
                        type="ERROR",
                        payload={"error": f"Unknown message type: {message.type}"},
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        message_id=f"error_{datetime.now(timezone.utc).timestamp()}"
                    )
                    await websocket_manager.send_personal_message(error_message.model_dump(), websocket)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_message = ErrorMessage(
                    type="ERROR",
                    payload={"error": "Invalid JSON format"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    message_id=f"error_{datetime.now(timezone.utc).timestamp()}"
                )
                await websocket_manager.send_personal_message(error_message.model_dump(), websocket)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_message = ErrorMessage(
                    type="ERROR",
                    payload={"error": "Internal server error"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    message_id=f"error_{datetime.now(timezone.utc).timestamp()}"
                )
                await websocket_manager.send_personal_message(error_message.model_dump(), websocket)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {websocket.client}")
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

async def handle_analytics_query(message: WebSocketMessage, websocket: WebSocket):
    """
    Handle analytics query using ReAct agent.
    
    Args:
        message: WebSocket message containing the query
        websocket: WebSocket connection
    """
    try:
        # Extract query from message payload or content
        query_data = getattr(message, 'payload', None) or getattr(message, 'content', {})
        if isinstance(query_data, str):
            user_query = query_data
            user_id = "anonymous"
        else:
            user_query = query_data.get("query", "")
            user_id = query_data.get("userId", "anonymous")
        
        logger.debug(f"Extracted query: '{user_query}' from payload: {query_data}")
        
        if not user_query.strip():
            raise ValueError("Empty query provided")
        
        logger.info(f"Processing query from {user_id}: {user_query}")
        
        # Send status update
        status_message = StatusUpdateMessage(
            type="STATUS_UPDATE",
            payload={"status": "processing", "message": "Processing your query..."},
            timestamp=datetime.now(timezone.utc).isoformat(),
            message_id=f"status_{datetime.now(timezone.utc).timestamp()}"
        )
        await websocket_manager.send_personal_message(status_message.model_dump(), websocket)
        
        # Process query using ReAct agent
        if react_agent is None:
            raise RuntimeError("ReAct agent not initialized")
        
        # Execute the agent workflow
        result = await react_agent.process_query(
            user_query=user_query,
            session_id=user_id or "default"
        )
        
        # Send response using frontend-expected format
        if result.get("error"):
            # Handle error case
            response_message = {
                "type": "agent_response",
                "payload": {
                    "type": "error",
                    "response": result.get("response", "An error occurred processing your query"),
                    "data": [],
                    "ui_resource": None,
                    "sql_query": None,
                    "reasoning": result.get("error")
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": f"response_{datetime.now(timezone.utc).timestamp()}"
            }
        else:
            # Handle successful case
            response_message = {
                "type": "agent_response",
                "payload": {
                    "type": "data",
                    "response": result.get("response", result.get("reasoning", "Query processed successfully")),
                    "data": result.get("data", []),
                    "ui_resource": result.get("ui_resource"),
                    "sql_query": result.get("sql_query"),
                    "reasoning": result.get("reasoning")
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": f"response_{datetime.now(timezone.utc).timestamp()}"
            }
        
        await websocket_manager.send_personal_message(response_message, websocket)
        logger.info(f"Query processed successfully for {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing analytics query: {e}")
        
        # Send error response
        error_message = ErrorMessage(
            type="ERROR",
            payload={
                "error": str(e),
                "query": message.payload.get("query", ""),
                "user_id": message.payload.get("userId", "anonymous")
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            message_id=f"error_{datetime.now(timezone.utc).timestamp()}"
        )
        
        await websocket_manager.send_personal_message(error_message.model_dump(), websocket)

# API endpoints for testing and debugging
@app.get("/api/status")
async def get_status():
    """Get system status and MCP server information."""
    try:
        # Get available tools from MCP servers
        database_tools = await mcp_manager.get_available_tools("database")
        
        return {
            "status": "operational",
            "mcp_servers": {
                "database": {
                    "connected": len(database_tools) > 0,
                    "tools": [tool.get("name", "") for tool in database_tools]
                }
            },
            "websocket_connections": len(websocket_manager.active_connections),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-query")
async def test_query(query: str, user_id: str = "test_user"):
    """Test endpoint for analytics queries (for debugging)."""
    try:
        if react_agent is None:
            raise HTTPException(status_code=500, detail="ReAct agent not initialized")
        
        result = await react_agent.process_query(
            user_query=query,
            session_id=user_id or "default"
        )
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error in test query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
