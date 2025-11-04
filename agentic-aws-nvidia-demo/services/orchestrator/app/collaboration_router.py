"""
Collaboration API endpoints and WebSocket handler.
"""
import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from .database import db
from .collaboration_websocket import manager, MessageType, lock_cleanup_task
from .collaboration_crud import (
    create_story_permission, get_story_permissions,
    check_story_permission, create_comment, get_story_comments,
    delete_comment
)
from .collaboration_models import StoryPermissionRole
from .crud import get_story
from .logger import logger
import asyncio

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


# Request/Response Models
class ShareStoryReq(BaseModel):
    story_id: int
    user_id: int
    role: str = Field(..., pattern="^(owner|editor|viewer)$")


class CommentCreateReq(BaseModel):
    story_id: int
    content: str
    beat_id: Optional[int] = None
    scene_id: Optional[int] = None
    parent_comment_id: Optional[int] = None


class BeatLockReq(BaseModel):
    beat_id: int
    duration_minutes: int = Field(30, ge=1, le=120)


# WebSocket endpoint
@router.websocket("/ws/story/{story_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    story_id: int,
    user_id: int = Query(...),
    user_name: str = Query("User"),
    user_email: str = Query("user@example.com")
):
    """
    WebSocket endpoint for real-time collaboration on a story.
    
    Query params:
    - user_id: User ID
    - user_name: User display name
    - user_email: User email
    """
    # TODO: In production, authenticate user via token/JWT
    # For now, accept user info from query params
    
    await manager.connect(websocket, story_id, user_id, user_name, user_email)
    
    try:
        # Send initial presence list
        users = manager.get_room_users(story_id)
        await websocket.send_json({
            "type": "presence_update",
            "users": users
        })
        
        # Send initial locks state
        # This would query database for persistent locks
        await websocket.send_json({
            "type": "initial_state",
            "story_id": story_id,
            "users": users
        })
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                conn_info = manager.connection_info.get(websocket, {})
                current_user_id = conn_info.get("user_id")
                
                # Handle different message types
                if msg_type == MessageType.EDIT:
                    # Beat edit
                    beat_id = message.get("beat_id")
                    changes = message.get("changes", {})
                    
                    # Check if user has edit permission
                    # TODO: Check permission from database
                    # For now, allow if in room
                    
                    # Check lock
                    lock_holder = manager.get_beat_lock(beat_id)
                    if lock_holder and lock_holder != current_user_id:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Beat {beat_id} is locked by another user"
                        })
                        continue
                    
                    # Broadcast edit to others
                    await manager.broadcast(
                        story_id,
                        {
                            "type": MessageType.EDIT,
                            "beat_id": beat_id,
                            "changes": changes,
                            "user_id": current_user_id,
                            "user_name": conn_info.get("user_name")
                        },
                        exclude=websocket
                    )
                    
                    # Send notification
                    await manager.broadcast(
                        story_id,
                        {
                            "type": MessageType.NOTIFICATION,
                            "message": f"{conn_info.get('user_name')} edited Beat {beat_id}",
                            "timestamp": message.get("timestamp")
                        }
                    )
                
                elif msg_type == MessageType.CURSOR_MOVE:
                    # Cursor position update
                    await manager.broadcast(
                        story_id,
                        {
                            "type": MessageType.CURSOR_MOVE,
                            "beat_id": message.get("beat_id"),
                            "position": message.get("position"),
                            "user_id": current_user_id,
                            "user_name": conn_info.get("user_name")
                        },
                        exclude=websocket
                    )
                
                elif msg_type == MessageType.BEAT_LOCK:
                    # Request beat lock
                    beat_id = message.get("beat_id")
                    duration = message.get("duration_minutes", 30)
                    
                    if manager.lock_beat(beat_id, current_user_id, duration):
                        # Success - broadcast lock
                        await manager.broadcast(
                            story_id,
                            {
                                "type": MessageType.BEAT_LOCK,
                                "beat_id": beat_id,
                                "locked_by": current_user_id,
                                "locked_by_name": conn_info.get("user_name"),
                                "expires_at": manager.lock_expires.get(beat_id).isoformat() if beat_id in manager.lock_expires else None
                            }
                        )
                    else:
                        # Failed - already locked
                        locked_by = manager.get_beat_lock(beat_id)
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Beat {beat_id} is already locked",
                            "locked_by": locked_by
                        })
                
                elif msg_type == MessageType.BEAT_UNLOCK:
                    # Release beat lock
                    beat_id = message.get("beat_id")
                    lock_holder = manager.get_beat_lock(beat_id)
                    
                    if lock_holder == current_user_id:
                        manager.release_beat_lock(beat_id)
                        await manager.broadcast(
                            story_id,
                            {
                                "type": MessageType.BEAT_UNLOCK,
                                "beat_id": beat_id,
                                "unlocked_by": current_user_id
                            }
                        )
                
                elif msg_type == MessageType.CHAT:
                    # Chat message
                    chat_message = message.get("message", "")
                    
                    await manager.broadcast(
                        story_id,
                        {
                            "type": MessageType.CHAT,
                            "message": chat_message,
                            "user_id": current_user_id,
                            "user_name": conn_info.get("user_name"),
                            "timestamp": message.get("timestamp")
                        }
                    )
                
                elif msg_type == MessageType.COMMENT:
                    # Comment created/updated
                    await manager.broadcast(
                        story_id,
                        {
                            "type": MessageType.COMMENT,
                            "comment": message.get("comment"),
                            "action": message.get("action", "created"),
                            "user_id": current_user_id,
                            "user_name": conn_info.get("user_name")
                        },
                        exclude=websocket
                    )
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": "Internal server error"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


# REST endpoints for collaboration
@router.post("/stories/{story_id}/share")
async def share_story(
    story_id: int,
    req: ShareStoryReq,
    session: AsyncSession = Depends(db.get_db_session),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Share a story with another user."""
    try:
        # Check if current user has owner permission
        has_permission = await check_story_permission(
            session, story_id, current_user_id, StoryPermissionRole.OWNER
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only story owners can share stories"
            )
        
        role = StoryPermissionRole[req.role.upper()]
        permission = await create_story_permission(
            session,
            story_id=story_id,
            user_id=req.user_id,
            role=role,
            invited_by=current_user_id
        )
        
        return {
            "story_id": permission.story_id,
            "user_id": permission.user_id,
            "role": permission.role.value,
            "invited_by": permission.invited_by
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sharing story: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share story"
        )


@router.get("/stories/{story_id}/permissions")
async def get_permissions(
    story_id: int,
    session: AsyncSession = Depends(db.get_db_session),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Get all permissions for a story."""
    try:
        # Check permission
        has_permission = await check_story_permission(
            session, story_id, current_user_id, StoryPermissionRole.VIEWER
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to view story"
            )
        
        permissions = await get_story_permissions(session, story_id)
        
        return {
            "permissions": [
                {
                    "user_id": p.user_id,
                    "role": p.role.value,
                    "invited_by": p.invited_by,
                    "created_at": p.created_at.isoformat()
                }
                for p in permissions
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get permissions"
        )


@router.post("/comments")
async def create_comment_endpoint(
    req: CommentCreateReq,
    session: AsyncSession = Depends(db.get_db_session),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create a comment."""
    try:
        # Check permission
        has_permission = await check_story_permission(
            session, req.story_id, current_user_id, StoryPermissionRole.VIEWER
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to comment"
            )
        
        comment = await create_comment(
            session,
            story_id=req.story_id,
            user_id=current_user_id,
            content=req.content,
            beat_id=req.beat_id,
            scene_id=req.scene_id,
            parent_comment_id=req.parent_comment_id
        )
        
        return {
            "id": comment.id,
            "content": comment.content,
            "user_id": comment.user_id,
            "beat_id": comment.beat_id,
            "scene_id": comment.scene_id,
            "created_at": comment.created_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment"
        )


@router.get("/stories/{story_id}/comments")
async def get_comments(
    story_id: int,
    beat_id: Optional[int] = Query(None),
    scene_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(db.get_db_session),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Get comments for a story."""
    try:
        # Check permission
        has_permission = await check_story_permission(
            session, story_id, current_user_id, StoryPermissionRole.VIEWER
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to view story"
            )
        
        comments = await get_story_comments(session, story_id, beat_id, scene_id)
        
        return {
            "comments": [
                {
                    "id": c.id,
                    "content": c.content,
                    "user_id": c.user_id,
                    "beat_id": c.beat_id,
                    "scene_id": c.scene_id,
                    "parent_comment_id": c.parent_comment_id,
                    "resolved": c.resolved,
                    "created_at": c.created_at.isoformat()
                }
                for c in comments
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comments"
        )
