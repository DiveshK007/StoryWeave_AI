"""
WebSocket management for real-time collaboration.
"""
import json
import asyncio
from typing import Dict, Set, Optional, List
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from .logger import logger
from .models import Story, Beat
from .crud import get_story


class ConnectionManager:
    """Manages WebSocket connections for story rooms."""
    
    def __init__(self):
        # story_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> user_info
        self.connection_info: Dict[WebSocket, Dict] = {}
        # beat_id -> user_id (who has lock)
        self.beat_locks: Dict[int, int] = {}
        # beat_id -> expires_at
        self.lock_expires: Dict[int, datetime] = {}
        # user_id -> Set[WebSocket] (multiple tabs/devices)
        self.user_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, story_id: int, user_id: int, user_name: str, user_email: str):
        """Connect a user to a story room."""
        await websocket.accept()
        
        if story_id not in self.active_connections:
            self.active_connections[story_id] = set()
        
        self.active_connections[story_id].add(websocket)
        self.connection_info[websocket] = {
            "story_id": story_id,
            "user_id": user_id,
            "user_name": user_name,
            "user_email": user_email,
            "connected_at": datetime.utcnow()
        }
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        # Notify others of new user
        await self.broadcast_presence_update(story_id, websocket)
        
        logger.info(f"User {user_id} connected to story {story_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a user from a story room."""
        info = self.connection_info.pop(websocket, None)
        if not info:
            return
        
        story_id = info["story_id"]
        user_id = info["user_id"]
        
        # Remove from story room
        if story_id in self.active_connections:
            self.active_connections[story_id].discard(websocket)
            if not self.active_connections[story_id]:
                del self.active_connections[story_id]
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Release locks held by this user
        locks_to_release = [
            beat_id for beat_id, locked_user_id in self.beat_locks.items()
            if locked_user_id == user_id
        ]
        for beat_id in locks_to_release:
            self.release_beat_lock(beat_id)
        
        logger.info(f"User {user_id} disconnected from story {story_id}")
    
    async def broadcast(self, story_id: int, message: dict, exclude: Optional[WebSocket] = None):
        """Broadcast message to all connections in a story room."""
        if story_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections[story_id]:
            if connection == exclude:
                continue
            
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_presence_update(self, story_id: int, exclude: Optional[WebSocket] = None):
        """Broadcast presence update (who's online)."""
        if story_id not in self.active_connections:
            return
        
        # Get unique users in room
        users = {}
        for conn in self.active_connections[story_id]:
            if conn == exclude:
                continue
            info = self.connection_info.get(conn)
            if info:
                user_id = info["user_id"]
                if user_id not in users:
                    users[user_id] = {
                        "user_id": user_id,
                        "user_name": info["user_name"],
                        "user_email": info["user_email"],
                        "connected_at": info["connected_at"].isoformat()
                    }
        
        message = {
            "type": "presence_update",
            "users": list(users.values())
        }
        
        await self.broadcast(story_id, message, exclude=exclude)
    
    def lock_beat(self, beat_id: int, user_id: int, duration_minutes: int = 30) -> bool:
        """Lock a beat for editing by a user."""
        # Check if already locked
        if beat_id in self.beat_locks:
            locked_by = self.beat_locks[beat_id]
            expires_at = self.lock_expires.get(beat_id)
            
            # Check if lock expired
            if expires_at and expires_at < datetime.utcnow():
                # Lock expired, can take it
                self.release_beat_lock(beat_id)
            elif locked_by != user_id:
                # Locked by someone else
                return False
        
        # Lock it
        self.beat_locks[beat_id] = user_id
        self.lock_expires[beat_id] = datetime.utcnow() + timedelta(minutes=duration_minutes)
        return True
    
    def release_beat_lock(self, beat_id: int):
        """Release a beat lock."""
        self.beat_locks.pop(beat_id, None)
        self.lock_expires.pop(beat_id, None)
    
    def get_beat_lock(self, beat_id: int) -> Optional[int]:
        """Get the user_id who has the lock, or None if not locked."""
        if beat_id in self.beat_locks:
            expires_at = self.lock_expires.get(beat_id)
            if expires_at and expires_at < datetime.utcnow():
                # Lock expired
                self.release_beat_lock(beat_id)
                return None
            return self.beat_locks[beat_id]
        return None
    
    def get_room_users(self, story_id: int) -> List[Dict]:
        """Get list of users currently in a story room."""
        if story_id not in self.active_connections:
            return []
        
        users = {}
        for conn in self.active_connections[story_id]:
            info = self.connection_info.get(conn)
            if info:
                user_id = info["user_id"]
                if user_id not in users:
                    users[user_id] = {
                        "user_id": user_id,
                        "user_name": info["user_name"],
                        "user_email": info["user_email"],
                        "connected_at": info["connected_at"].isoformat()
                    }
        
        return list(users.values())
    
    async def cleanup_expired_locks(self):
        """Cleanup expired locks (call periodically)."""
        now = datetime.utcnow()
        expired_locks = [
            beat_id for beat_id, expires_at in self.lock_expires.items()
            if expires_at < now
        ]
        for beat_id in expired_locks:
            self.release_beat_lock(beat_id)
            # Notify room that lock was released
            info = next(iter(self.connection_info.values()), None)
            if info:
                await self.broadcast(info["story_id"], {
                    "type": "beat_lock_released",
                    "beat_id": beat_id
                })


# Global connection manager instance
manager = ConnectionManager()


# Background task to cleanup expired locks
async def lock_cleanup_task():
    """Background task to periodically cleanup expired locks."""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            await manager.cleanup_expired_locks()
        except Exception as e:
            logger.error(f"Error in lock cleanup task: {e}")


# Message types for WebSocket communication
class MessageType:
    EDIT = "edit"
    CURSOR_MOVE = "cursor_move"
    PRESENCE = "presence"
    CHAT = "chat"
    BEAT_LOCK = "beat_lock"
    BEAT_UNLOCK = "beat_unlock"
    COMMENT = "comment"
    NOTIFICATION = "notification"
