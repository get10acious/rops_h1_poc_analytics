"""
RewardOps Analytics POC - FastAPI Backend

This is the main FastAPI application that serves as the MCP Host & Orchestrator
for the natural language analytics system.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from mcp_multi_client import mcp_manager
from langgraph_agent import create_react_agent
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
    level=getattr(logging, settings.LOG_LEVEL.upper()),
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
    logger.info("Starting RewardOps Analytics POC Backend...")
    
    try:
        # Initialize MCP clients
        await mcp_manager.initialize()
        logger.info("MCP clients initialized successfully")
        
        # Initialize ReAct agent
        global react_agent
        react_agent = create_react_agent()
        logger.info("ReAct agent initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down RewardOps Analytics POC Backend...")
        await mcp_manager.close_all()
        logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="RewardOps Analytics POC",
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
        "timestamp": datetime.utcnow().isoformat(),
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
            timestamp=datetime.utcnow().isoformat(),
            message_id=f"status_{datetime.utcnow().timestamp()}"
        )
        await websocket_manager.send_personal_message(status_message.dict(), websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                message = WebSocketMessage(**message_data)
                
                logger.info(f"Received message: {message.type} from {websocket.client}")
                
                # Handle different message types
                if message.type == "QUERY":
                    await handle_analytics_query(message, websocket)
                elif message.type == "PING":
                    # Respond to ping with pong
                    pong_message = StatusUpdateMessage(
                        type="STATUS_UPDATE",
                        payload={"status": "pong", "timestamp": datetime.utcnow().isoformat()},
                        timestamp=datetime.utcnow().isoformat(),
                        message_id=f"pong_{datetime.utcnow().timestamp()}"
                    )
                    await websocket_manager.send_personal_message(pong_message.dict(), websocket)
                else:
                    # Unknown message type
                    error_message = ErrorMessage(
                        type="ERROR",
                        payload={"error": f"Unknown message type: {message.type}"},
                        timestamp=datetime.utcnow().isoformat(),
                        message_id=f"error_{datetime.utcnow().timestamp()}"
                    )
                    await websocket_manager.send_personal_message(error_message.dict(), websocket)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_message = ErrorMessage(
                    type="ERROR",
                    payload={"error": "Invalid JSON format"},
                    timestamp=datetime.utcnow().isoformat(),
                    message_id=f"error_{datetime.utcnow().timestamp()}"
                )
                await websocket_manager.send_personal_message(error_message.dict(), websocket)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_message = ErrorMessage(
                    type="ERROR",
                    payload={"error": "Internal server error"},
                    timestamp=datetime.utcnow().isoformat(),
                    message_id=f"error_{datetime.utcnow().timestamp()}"
                )
                await websocket_manager.send_personal_message(error_message.dict(), websocket)
                
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
        # Extract query from message payload
        query_data = message.payload
        user_query = query_data.get("query", "")
        user_id = query_data.get("userId", "anonymous")
        
        if not user_query.strip():
            raise ValueError("Empty query provided")
        
        logger.info(f"Processing query from {user_id}: {user_query}")
        
        # Send status update
        status_message = StatusUpdateMessage(
            type="STATUS_UPDATE",
            payload={"status": "processing", "message": "Processing your query..."},
            timestamp=datetime.utcnow().isoformat(),
            message_id=f"status_{datetime.utcnow().timestamp()}"
        )
        await websocket_manager.send_personal_message(status_message.dict(), websocket)
        
        # Process query using ReAct agent
        if react_agent is None:
            raise RuntimeError("ReAct agent not initialized")
        
        # Execute the agent workflow
        result = await react_agent.ainvoke({
            "query": user_query,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send response
        response_message = ResponseMessage(
            type="RESPONSE",
            payload={
                "result": result.get("data", []),
                "visualization": result.get("visualization"),
                "query": user_query,
                "query_id": result.get("query_id", f"query_{datetime.utcnow().timestamp()}"),
                "processing_time": result.get("processing_time", 0)
            },
            timestamp=datetime.utcnow().isoformat(),
            message_id=f"response_{datetime.utcnow().timestamp()}"
        )
        
        await websocket_manager.send_personal_message(response_message.dict(), websocket)
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
            timestamp=datetime.utcnow().isoformat(),
            message_id=f"error_{datetime.utcnow().timestamp()}"
        )
        
        await websocket_manager.send_personal_message(error_message.dict(), websocket)

# API endpoints for testing and debugging
@app.get("/api/status")
async def get_status():
    """Get system status and MCP server information."""
    try:
        # Get available tools from MCP servers
        database_tools = await mcp_manager.get_available_tools("database")
        vizro_tools = await mcp_manager.get_available_tools("vizro")
        
        return {
            "status": "operational",
            "mcp_servers": {
                "database": {
                    "connected": len(database_tools) > 0,
                    "tools": [tool.name for tool in database_tools]
                },
                "vizro": {
                    "connected": len(vizro_tools) > 0,
                    "tools": [tool.name for tool in vizro_tools]
                }
            },
            "websocket_connections": len(websocket_manager.active_connections),
            "timestamp": datetime.utcnow().isoformat()
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
        
        result = await react_agent.ainvoke({
            "query": query,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in test query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
