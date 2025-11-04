"""
Database models for collaboration features.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer, String, Text, DateTime, ForeignKey,
    Index, Boolean, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .models import BaseModel, Base
import enum


class StoryPermissionRole(str, enum.Enum):
    """Story permission role enumeration."""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class StoryPermission(BaseModel):
    """Story permission model for sharing and collaboration."""
    __tablename__ = "story_permissions"
    
    story_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[StoryPermissionRole] = mapped_column(
        SQLEnum(StoryPermissionRole),
        nullable=False,
        default=StoryPermissionRole.VIEWER
    )
    invited_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="permissions")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    inviter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[invited_by])
    
    __table_args__ = (
        Index("idx_story_permission_story_user", "story_id", "user_id", unique=True),
    )
    
    def __repr__(self):
        return f"<StoryPermission(story_id={self.story_id}, user_id={self.user_id}, role={self.role.value})>"


class BeatLock(BaseModel):
    """Beat lock model to prevent simultaneous edits."""
    __tablename__ = "beat_locks"
    
    beat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("beats.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    locked_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    locked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )
    
    # Relationships
    beat: Mapped["Beat"] = relationship("Beat", back_populates="lock")
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"<BeatLock(beat_id={self.beat_id}, locked_by={self.locked_by})>"


class StoryComment(BaseModel):
    """Comment model for beats and scenes."""
    __tablename__ = "story_comments"
    
    story_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    beat_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("beats.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    scene_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("story_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="comments")
    beat: Mapped[Optional["Beat"]] = relationship("Beat", back_populates="comments")
    scene: Mapped[Optional["Scene"]] = relationship("Scene", back_populates="comments")
    user: Mapped["User"] = relationship("User")
    parent_comment: Mapped[Optional["StoryComment"]] = relationship(
        "StoryComment",
        remote_side="StoryComment.id",
        back_populates="replies"
    )
    replies: Mapped[list["StoryComment"]] = relationship(
        "StoryComment",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index("idx_comment_story_beat", "story_id", "beat_id"),
        Index("idx_comment_story_scene", "story_id", "scene_id"),
    )
    
    def __repr__(self):
        return f"<StoryComment(id={self.id}, story_id={self.story_id}, user_id={self.user_id})>"


# Update Story model to include relationships (done via relationship definitions)
# Update Beat model to include lock and comments (done via relationship definitions)
# Update Scene model to include comments (done via relationship definitions)
