"""
CRUD operations for StoryWeave AI database models.

All functions use async SQLAlchemy sessions.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import (
    User, Project, Story, Beat, Scene, CorpusDocument,
    StoryStatus, Character, CharacterMention, CharacterRelationship
)
from .logger import logger


# User CRUD
async def create_user(
    session: AsyncSession,
    email: str,
    password_hash: str
) -> User:
    """Create a new user."""
    user = User(email=email, password_hash=password_hash)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info(f"Created user: {user.email}")
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email."""
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


# Project CRUD
async def create_project(
    session: AsyncSession,
    user_id: int,
    name: str,
    description: Optional[str] = None
) -> Project:
    """Create a new project."""
    project = Project(user_id=user_id, name=name, description=description)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    logger.info(f"Created project: {project.name} (user_id={user_id})")
    return project


async def get_user_projects(
    session: AsyncSession,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Project]:
    """Get all projects for a user."""
    result = await session.execute(
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_project(
    session: AsyncSession,
    project_id: int,
    user_id: Optional[int] = None
) -> Optional[Project]:
    """Get a project by ID, optionally checking user ownership."""
    query = select(Project).where(Project.id == project_id)
    if user_id:
        query = query.where(Project.user_id == user_id)
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def delete_project(
    session: AsyncSession,
    project_id: int,
    user_id: Optional[int] = None
) -> bool:
    """Delete a project and all related data (cascade)."""
    project = await get_project(session, project_id, user_id)
    if not project:
        return False
    
    await session.delete(project)
    await session.commit()
    logger.info(f"Deleted project: {project_id}")
    return True


# Story CRUD
async def create_story(
    session: AsyncSession,
    project_id: int,
    premise: str,
    genre: Optional[str] = None,
    length: Optional[str] = None,
    logline: Optional[str] = None,
    status: StoryStatus = StoryStatus.DRAFT,
    beats_data: Optional[List[Dict[str, Any]]] = None
) -> Story:
    """
    Create a new story with optional beats.
    
    Args:
        session: Database session
        project_id: Project ID
        premise: Story premise
        genre: Story genre
        length: Story length (short/feature/long)
        logline: Story logline
        status: Story status
        beats_data: List of beat dictionaries with keys: beat_index, title, goal, conflict, outcome
    
    Returns:
        Created Story object with beats loaded
    """
    story = Story(
        project_id=project_id,
        premise=premise,
        genre=genre,
        length=length,
        logline=logline,
        status=status
    )
    session.add(story)
    await session.flush()  # Flush to get story.id
    
    # Create beats if provided
    if beats_data:
        for beat_data in beats_data:
            beat = Beat(
                story_id=story.id,
                beat_index=beat_data.get("beat_index", 0),
                title=beat_data.get("title", ""),
                goal=beat_data.get("goal"),
                conflict=beat_data.get("conflict"),
                outcome=beat_data.get("outcome")
            )
            session.add(beat)
    
    await session.commit()
    await session.refresh(story)
    
    # Load relationships
    await session.refresh(story, ["beats"])
    
    logger.info(f"Created story: {story.id} (project_id={project_id})")
    return story


async def get_user_stories(
    session: AsyncSession,
    user_id: int,
    project_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Story]:
    """
    Get all stories for a user, optionally filtered by project.
    
    Returns stories with beats and project relationships loaded.
    """
    query = (
        select(Story)
        .join(Project)
        .where(Project.user_id == user_id)
        .options(selectinload(Story.beats), selectinload(Story.project))
    )
    
    if project_id:
        query = query.where(Story.project_id == project_id)
    
    query = query.order_by(Story.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_story(
    session: AsyncSession,
    story_id: int,
    user_id: Optional[int] = None
) -> Optional[Story]:
    """Get a story by ID with all relationships loaded."""
    query = select(Story).where(Story.id == story_id)
    
    if user_id:
        query = query.join(Project).where(Project.user_id == user_id)
    
    query = query.options(
        selectinload(Story.beats).selectinload(Beat.scenes),
        selectinload(Story.project)
    )
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def update_story(
    session: AsyncSession,
    story_id: int,
    **kwargs
) -> Optional[Story]:
    """Update story fields."""
    story = await get_story(session, story_id)
    if not story:
        return None
    
    for key, value in kwargs.items():
        if hasattr(story, key) and key != "id":
            setattr(story, key, value)
    
    story.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(story)
    logger.info(f"Updated story: {story_id}")
    return story


# Beat CRUD
async def create_beat(
    session: AsyncSession,
    story_id: int,
    beat_index: int,
    title: str,
    goal: Optional[str] = None,
    conflict: Optional[str] = None,
    outcome: Optional[str] = None
) -> Beat:
    """Create a new beat."""
    beat = Beat(
        story_id=story_id,
        beat_index=beat_index,
        title=title,
        goal=goal,
        conflict=conflict,
        outcome=outcome
    )
    session.add(beat)
    await session.commit()
    await session.refresh(beat)
    logger.info(f"Created beat: {beat.title} (story_id={story_id})")
    return beat


async def get_story_beats(
    session: AsyncSession,
    story_id: int
) -> List[Beat]:
    """Get all beats for a story, ordered by beat_index."""
    result = await session.execute(
        select(Beat)
        .where(Beat.story_id == story_id)
        .order_by(Beat.beat_index)
        .options(selectinload(Beat.scenes))
    )
    return list(result.scalars().all())


# Scene CRUD
async def create_scene(
    session: AsyncSession,
    beat_id: int,
    text: str,
    version: int = 1
) -> Scene:
    """Create a new scene."""
    scene = Scene(beat_id=beat_id, text=text, version=version)
    session.add(scene)
    await session.commit()
    await session.refresh(scene)
    logger.info(f"Created scene: {scene.id} (beat_id={beat_id}, version={version})")
    return scene


async def update_scene(
    session: AsyncSession,
    scene_id: int,
    text: Optional[str] = None,
    version: Optional[int] = None
) -> Optional[Scene]:
    """Update a scene or create a new version."""
    scene = await session.get(Scene, scene_id)
    if not scene:
        return None
    
    if text is not None:
        scene.text = text
    if version is not None:
        scene.version = version
    
    scene.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(scene)
    logger.info(f"Updated scene: {scene_id}")
    return scene


async def get_beat_scenes(
    session: AsyncSession,
    beat_id: int,
    latest_only: bool = False
) -> List[Scene]:
    """Get scenes for a beat, optionally only the latest version."""
    query = select(Scene).where(Scene.beat_id == beat_id)
    
    if latest_only:
        # Get the latest version for each scene
        subquery = (
            select(Scene.beat_id, func.max(Scene.version).label("max_version"))
            .where(Scene.beat_id == beat_id)
            .group_by(Scene.beat_id)
            .subquery()
        )
        query = query.join(
            subquery,
            (Scene.beat_id == subquery.c.beat_id) &
            (Scene.version == subquery.c.max_version)
        )
    
    query = query.order_by(Scene.created_at.desc())
    
    result = await session.execute(query)
    return list(result.scalars().all())


# CorpusDocument CRUD
async def create_corpus_document(
    session: AsyncSession,
    project_id: int,
    filename: str,
    content: str,
    chunk_count: int = 0
) -> CorpusDocument:
    """Create a new corpus document."""
    doc = CorpusDocument(
        project_id=project_id,
        filename=filename,
        content=content,
        chunk_count=chunk_count
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    logger.info(f"Created corpus document: {filename} (project_id={project_id})")
    return doc


async def get_project_corpus_documents(
    session: AsyncSession,
    project_id: int
) -> List[CorpusDocument]:
    """Get all corpus documents for a project."""
    result = await session.execute(
        select(CorpusDocument)
        .where(CorpusDocument.project_id == project_id)
        .order_by(CorpusDocument.created_at.desc())
    )
    return list(result.scalars().all())

