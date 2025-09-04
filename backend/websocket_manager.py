"""
WebSocket connection manager for RewardOps Analytics POC.

This module handles WebSocket connections, message broadcasting, and connection
lifecycle management.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket
from collections import defaultdict

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Active connections: {websocket: connection_info}
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        # Connection statistics
        self.stats = {
            "total_connections": 0,
            "total_messages": 0,
            "active_connections": 0
        }
        # Message history for debugging
        self.message_history: List[Dict[str, Any]] = []
        # Rate limiting per connection
        self.rate_limits: Dict[WebSocket, Dict[str, Any]] = defaultdict(lambda: {
            "requests": 0,
            "window_start": datetime.utcnow(),
            "last_request": datetime.utcnow()
        })
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        try:
            await websocket.accept()
            
            # Store connection info
            connection_info = {
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "user_id": None,
                "message_count": 0
            }
            
            self.active_connections[websocket] = connection_info
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            logger.info(f"WebSocket connected: {websocket.client}. Total connections: {self.stats['active_connections']}")
            
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}")
            raise
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            connection_info = self.active_connections[websocket]
            duration = datetime.utcnow() - connection_info["connected_at"]
            
            logger.info(f"WebSocket disconnected: {websocket.client}. Duration: {duration}")
            
            # Clean up
            del self.active_connections[websocket]
            if websocket in self.rate_limits:
                del self.rate_limits[websocket]
            
            self.stats["active_connections"] -= 1
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """Send a message to a specific WebSocket connection."""
        try:
            if websocket in self.active_connections:
                await websocket.send_text(json.dumps(message))
                
                # Update connection info
                self.active_connections[websocket]["last_activity"] = datetime.utcnow()
                self.active_connections[websocket]["message_count"] += 1
                self.stats["total_messages"] += 1
                
                # Add to message history (keep last 100 messages)
                self.message_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": message.get("type", "unknown"),
                    "client": str(websocket.client),
                    "message_id": message.get("message_id", "unknown")
                })
                
                if len(self.message_history) > 100:
                    self.message_history.pop(0)
                
                logger.debug(f"Message sent to {websocket.client}: {message.get('type', 'unknown')}")
            else:
                logger.warning(f"Attempted to send message to disconnected WebSocket: {websocket.client}")
                
        except Exception as e:
            logger.error(f"Error sending message to WebSocket {websocket.client}: {e}")
            # Remove the connection if it's no longer valid
            self.disconnect(websocket)
    
    async def broadcast_message(self, message: Dict[str, Any], exclude: Optional[WebSocket] = None) -> None:
        """Broadcast a message to all connected WebSockets."""
        if not self.active_connections:
            logger.warning("No active connections to broadcast to")
            return
        
        disconnected_connections = []
        
        for websocket in self.active_connections:
            if exclude and websocket == exclude:
                continue
            
            try:
                await websocket.send_text(json.dumps(message))
                self.active_connections[websocket]["last_activity"] = datetime.utcnow()
                self.stats["total_messages"] += 1
                
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket {websocket.client}: {e}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            self.disconnect(websocket)
        
        logger.info(f"Message broadcasted to {len(self.active_connections)} connections")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """Send a message to all connections for a specific user."""
        sent_count = 0
        
        for websocket, connection_info in self.active_connections.items():
            if connection_info.get("user_id") == user_id:
                try:
                    await websocket.send_text(json.dumps(message))
                    connection_info["last_activity"] = datetime.utcnow()
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    self.disconnect(websocket)
        
        logger.info(f"Message sent to {sent_count} connections for user {user_id}")
    
    def set_user_id(self, websocket: WebSocket, user_id: str) -> None:
        """Associate a user ID with a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections[websocket]["user_id"] = user_id
            logger.info(f"User ID {user_id} associated with WebSocket {websocket.client}")
    
    def get_connection_info(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        """Get connection information for a WebSocket."""
        return self.active_connections.get(websocket)
    
    def get_all_connections(self) -> Dict[WebSocket, Dict[str, Any]]:
        """Get all active connections."""
        return self.active_connections.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            **self.stats,
            "average_messages_per_connection": (
                self.stats["total_messages"] / max(self.stats["total_connections"], 1)
            ),
            "oldest_connection": min(
                (info["connected_at"] for info in self.active_connections.values()),
                default=None
            ),
            "newest_connection": max(
                (info["connected_at"] for info in self.active_connections.values()),
                default=None
            )
        }
    
    def check_rate_limit(self, websocket: WebSocket, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Check if a WebSocket connection is within rate limits."""
        if websocket not in self.rate_limits:
            return True
        
        now = datetime.utcnow()
        rate_limit_info = self.rate_limits[websocket]
        
        # Reset window if needed
        if (now - rate_limit_info["window_start"]).total_seconds() > window_seconds:
            rate_limit_info["requests"] = 0
            rate_limit_info["window_start"] = now
        
        # Check if under limit
        if rate_limit_info["requests"] >= max_requests:
            return False
        
        # Increment request count
        rate_limit_info["requests"] += 1
        rate_limit_info["last_request"] = now
        
        return True
    
    def get_rate_limit_info(self, websocket: WebSocket) -> Dict[str, Any]:
        """Get rate limit information for a WebSocket connection."""
        if websocket not in self.rate_limits:
            return {"requests": 0, "window_start": None, "last_request": None}
        
        return self.rate_limits[websocket].copy()
    
    async def cleanup_stale_connections(self, timeout_seconds: int = 3600) -> None:
        """Remove stale connections that haven't been active for a while."""
        now = datetime.utcnow()
        stale_connections = []
        
        for websocket, connection_info in self.active_connections.items():
            time_since_activity = (now - connection_info["last_activity"]).total_seconds()
            if time_since_activity > timeout_seconds:
                stale_connections.append(websocket)
        
        for websocket in stale_connections:
            logger.info(f"Removing stale connection: {websocket.client}")
            self.disconnect(websocket)
        
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")
    
    async def start_heartbeat(self, interval_seconds: int = 30) -> None:
        """Start heartbeat mechanism to keep connections alive."""
        while True:
            try:
                # Send ping to all connections
                ping_message = {
                    "type": "PING",
                    "payload": {"timestamp": datetime.utcnow().isoformat()},
                    "timestamp": datetime.utcnow().isoformat(),
                    "message_id": f"ping_{datetime.utcnow().timestamp()}"
                }
                
                await self.broadcast_message(ping_message)
                
                # Clean up stale connections
                await self.cleanup_stale_connections()
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in heartbeat mechanism: {e}")
                await asyncio.sleep(interval_seconds)
    
    def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent message history."""
        return self.message_history[-limit:] if self.message_history else []
    
    def clear_message_history(self) -> None:
        """Clear message history."""
        self.message_history.clear()
        logger.info("Message history cleared")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
