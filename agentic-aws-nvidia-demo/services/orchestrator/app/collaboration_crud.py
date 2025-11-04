"""
CRUD operations for collaboration features.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import User, Story, Project
from .collaboration_models import (
    StoryPermission, StoryPermissionRole, BeatLock, StoryComment
)
from .logger import logger


# Permission CRUD
async def create_story_permission(
    session: AsyncSession,
    story_id: int,
    user_id: int,
    role: StoryPermissionRole,
    invited_by: Optional[int] = None
) -> StoryPermission:
    """Create a story permission (share story with user)."""
    # Check if permission already exists
    existing = await session.execute(
        select(StoryPermission).where(
            and_(
                StoryPermission.story_id == story_id,
                StoryPermission.user_id == user_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Permission already exists")
    
    permission = StoryPermission(
        story_id=story_id,
        user_id=user_id,
        role=role,
        invited_by=invited_by
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    logger.info(f"Created permission: story {story_id}, user {user_id}, role {role.value}")
    return permission


async def get_story_permissions(
    session: AsyncSession,
    story_id: int
) -> List[StoryPermission]:
    """Get all permissions for a story."""
    query = select(StoryPermission).where(
        StoryPermission.story_id == story_id
    )
    query = query.options(
        selectinload(StoryPermission.user),
        selectinload(StoryPermission.inviter)
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_user_story_permission(
    session: AsyncSession,
    story_id: int,
    user_id: int
) -> Optional[StoryPermission]:
    """Get a user's permission for a story."""
    query = select(StoryPermission).where(
        and_(
            StoryPermission.story_id == story_id,
            StoryPermission.user_id == user_id
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def check_story_permission(
    session: AsyncSession,
    story_id: int,
    user_id: int,
    required_role: StoryPermissionRole
) -> bool:
    """Check if user has required permission level for story."""
    # Owner of story's project always has owner permission
    story = await session.get(Story, story_id)
    if story:
        project = await session.get(Project, story.project_id)
        if project and project.user_id == user_id:
            return True
    
    # Check explicit permissions
    permission = await get_user_story_permission(session, story_id, user_id)
    if not permission:
        return False
    
    # Role hierarchy: owner > editor > viewer
    role_hierarchy = {
        StoryPermissionRole.VIEWER: 0,
        StoryPermissionRole.EDITOR: 1,
        StoryPermissionRole.OWNER: 2
    }
    
    user_role_level = role_hierarchy.get(permission.role, -1)
    required_role_level = role_hierarchy.get(required_role, 999)
    
    return user_role_level >= required_role_level


async def update_story_permission(
    session: AsyncSession,
    story_id: int,
    user_id: int,
    new_role: StoryPermissionRole
) -> Optional[StoryPermission]:
    """Update a story permission."""
    permission = await get_user_story_permission(session, story_id, user_id)
    if not permission:
        return None
    
    permission.role = new_role
    await session.commit()
    await session.refresh(permission)
    logger.info(f"Updated permission: story {story_id}, user {user_id}, role {new_role.value}")
    return permission


async def delete_story_permission(
    session: AsyncSession,
    story_id: int,
    user_id: int
) -> bool:
    """Remove a story permission (unshare)."""
    permission = await get_user_story_permission(session, story_id, user_id)
    if not permission:
        return False
    
    await session.delete(permission)
    await session.commit()
    logger.info(f"Deleted permission: story {story_id}, user {user_id}")
    return True


# Comment CRUD
async def create_comment(
    session: AsyncSession,
    story_id: int,
    user_id: int,
    content: str,
    beat_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    parent_comment_id: Optional[int] = None
) -> StoryComment:
    """Create a comment on a story, beat, or scene."""
    comment = StoryComment(
        story_id=story_id,
        user_id=user_id,
        content=content,
        beat_id=beat_id,
        scene_id=scene_id,
        parent_comment_id=parent_comment_id
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    logger.info(f"Created comment: {comment.id} on story {story_id}")
    return comment


async def get_story_comments(
    session: AsyncSession,
    story_id: int,
    beat_id: Optional[int] = None,
    scene_id: Optional[int] = None
) -> List[StoryComment]:
    """Get comments for a story, optionally filtered by beat or scene."""
    query = select(StoryComment).where(StoryComment.story_id == story_id)
    
    if beat_id:
        query = query.where(StoryComment.beat_id == beat_id)
    elif scene_id:
        query = query.where(StoryComment.scene_id == scene_id)
    else:
        # Top-level comments only (no beat_id or scene_id)
        query = query.where(
            and_(
                StoryComment.beat_id.is_(None),
                StoryComment.scene_id.is_(None)
            )
        )
    
    query = query.options(
        selectinload(StoryComment.user),
        selectinload(StoryComment.replies).selectinload(StoryComment.user)
    ).order_by(StoryComment.created_at.asc())
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_comment(
    session: AsyncSession,
    comment_id: int,
    content: Optional[str] = None,
    resolved: Optional[bool] = None
) -> Optional[StoryComment]:
    """Update a comment."""
    comment = await session.get(StoryComment, comment_id)
    if not comment:
        return None
    
    if content is not None:
        comment.content = content
    if resolved is not None:
        comment.resolved = resolved
    
    await session.commit()
    await session.refresh(comment)
    return comment


async def delete_comment(
    session: AsyncSession,
    comment_id: int
) -> bool:
    """Delete a comment (cascades to replies)."""
    comment = await session.get(StoryComment, comment_id)
    if not comment:
        return False
    
    await session.delete(comment)
    await session.commit()
    logger.info(f"Deleted comment: {comment_id}")
    return True
