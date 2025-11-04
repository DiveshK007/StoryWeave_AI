"""
SQLAlchemy models for StoryWeave AI.

All models use async SQLAlchemy with proper relationships and timestamps.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    Index, Boolean, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class StoryStatus(str, enum.Enum):
    """Story status enumeration."""
    DRAFT = "draft"
    OUTLINE = "outline"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class BaseModel(Base):
    """Base model with common fields."""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class User(BaseModel):
    """User model for authentication and ownership."""
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Project(BaseModel):
    """Project model for organizing stories."""
    __tablename__ = "projects"
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    stories: Mapped[list["Story"]] = relationship(
        "Story",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    corpus_documents: Mapped[list["CorpusDocument"]] = relationship(
        "CorpusDocument",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index("idx_project_user_created", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, user_id={self.user_id})>"


class Story(BaseModel):
    """Story model for storing story metadata and structure."""
    __tablename__ = "stories"
    
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    premise: Mapped[str] = mapped_column(Text, nullable=False)
    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    length: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    logline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[StoryStatus] = mapped_column(
        SQLEnum(StoryStatus),
        default=StoryStatus.DRAFT,
        nullable=False
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="stories")
    beats: Mapped[list["Beat"]] = relationship(
        "Beat",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="Beat.beat_index",
        lazy="selectin"
    )
    characters: Mapped[list["Character"]] = relationship(
        "Character",
        back_populates="story",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    permissions: Mapped[list["StoryPermission"]] = relationship(
        "StoryPermission",
        back_populates="story",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    comments: Mapped[list["StoryComment"]] = relationship(
        "StoryComment",
        back_populates="story",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index("idx_story_project_created", "project_id", "created_at"),
        Index("idx_story_status", "status"),
    )
    
    def __repr__(self):
        return f"<Story(id={self.id}, premise={self.premise[:50]}..., project_id={self.project_id})>"


class Beat(BaseModel):
    """Beat model for story structure beats."""
    __tablename__ = "beats"
    
    story_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    beat_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conflict: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="beats")
    scenes: Mapped[list["Scene"]] = relationship(
        "Scene",
        back_populates="beat",
        cascade="all, delete-orphan",
        order_by="Scene.created_at",
        lazy="selectin"
    )
    lock: Mapped[Optional["BeatLock"]] = relationship(
        "BeatLock",
        back_populates="beat",
        uselist=False,
        cascade="all, delete-orphan"
    )
    comments: Mapped[list["StoryComment"]] = relationship(
        "StoryComment",
        back_populates="beat",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index("idx_beat_story_index", "story_id", "beat_index"),
        Index("idx_beat_story_unique", "story_id", "beat_index", unique=True),
    )
    
    def __repr__(self):
        return f"<Beat(id={self.id}, title={self.title}, story_id={self.story_id}, index={self.beat_index})>"


class Scene(BaseModel):
    """Scene model for storing scene text with versioning."""
    __tablename__ = "scenes"
    
    beat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("beats.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    beat: Mapped["Beat"] = relationship("Beat", back_populates="scenes")
    character_mentions: Mapped[list["CharacterMention"]] = relationship(
        "CharacterMention",
        back_populates="scene",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    comments: Mapped[list["StoryComment"]] = relationship(
        "StoryComment",
        back_populates="scene",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index("idx_scene_beat_version", "beat_id", "version"),
    )
    
    def __repr__(self):
        return f"<Scene(id={self.id}, beat_id={self.beat_id}, version={self.version})>"


class CorpusDocument(BaseModel):
    """Corpus document model for storing reference documents."""
    __tablename__ = "corpus_documents"
    
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="corpus_documents")
    
    __table_args__ = (
        Index("idx_corpus_project_filename", "project_id", "filename"),
    )
    
    def __repr__(self):
        return f"<CorpusDocument(id={self.id}, filename={self.filename}, project_id={self.project_id})>"


class CharacterRole(str, enum.Enum):
    """Character role enumeration."""
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    MINOR = "minor"


class Character(BaseModel):
    """Character model for story characters."""
    __tablename__ = "characters"
    
    story_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[CharacterRole] = mapped_column(
        SQLEnum(CharacterRole),
        default=CharacterRole.SUPPORTING,
        nullable=False
    )
    profile_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string with character profile
    
    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="characters")
    mentions: Mapped[list["CharacterMention"]] = relationship(
        "CharacterMention",
        back_populates="character",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    relationships_a: Mapped[list["CharacterRelationship"]] = relationship(
        "CharacterRelationship",
        foreign_keys="CharacterRelationship.character_a_id",
        back_populates="character_a",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    relationships_b: Mapped[list["CharacterRelationship"]] = relationship(
        "CharacterRelationship",
        foreign_keys="CharacterRelationship.character_b_id",
        back_populates="character_b",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index("idx_character_story_name", "story_id", "name"),
    )
    
    def __repr__(self):
        return f"<Character(id={self.id}, name={self.name}, role={self.role.value}, story_id={self.story_id})>"


class RelationshipType(str, enum.Enum):
    """Relationship type enumeration."""
    FAMILY = "family"
    FRIEND = "friend"
    ENEMY = "enemy"
    ROMANCE = "romance"
    MENTOR = "mentor"
    RIVAL = "rival"
    ALLY = "ally"
    OTHER = "other"


class CharacterRelationship(BaseModel):
    """Character relationship model."""
    __tablename__ = "character_relationships"
    
    character_a_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    character_b_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[RelationshipType] = mapped_column(
        SQLEnum(RelationshipType),
        nullable=False
    )
    strength: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # 1-10 scale
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    character_a: Mapped["Character"] = relationship(
        "Character",
        foreign_keys=[character_a_id],
        back_populates="relationships_a"
    )
    character_b: Mapped["Character"] = relationship(
        "Character",
        foreign_keys=[character_b_id],
        back_populates="relationships_b"
    )
    
    __table_args__ = (
        Index("idx_relationship_characters", "character_a_id", "character_b_id"),
    )
    
    def __repr__(self):
        return f"<CharacterRelationship(id={self.id}, char_a={self.character_a_id}, char_b={self.character_b_id}, type={self.type.value})>"


class CharacterMention(BaseModel):
    """Character mention in scenes."""
    __tablename__ = "character_mentions"
    
    scene_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    context: Mapped[str] = mapped_column(Text, nullable=False)  # Excerpt where character is mentioned
    mention_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "dialogue", "action", "description"
    
    # Relationships
    scene: Mapped["Scene"] = relationship("Scene", back_populates="character_mentions")
    character: Mapped["Character"] = relationship("Character", back_populates="mentions")
    
    __table_args__ = (
        Index("idx_mention_scene_character", "scene_id", "character_id"),
    )
    
    def __repr__(self):
        return f"<CharacterMention(id={self.id}, scene_id={self.scene_id}, character_id={self.character_id})>"


# Update Story model to include characters relationship
# This needs to be done by updating the Story class

