"""
CRUD operations for character-related models.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import (
    Character, CharacterMention, CharacterRelationship,
    CharacterRole, RelationshipType, Scene
)
from .logger import logger
import json


# Character CRUD
async def create_character(
    session: AsyncSession,
    story_id: int,
    name: str,
    role: CharacterRole,
    profile_json: Dict[str, Any]
) -> Character:
    """Create a new character."""
    character = Character(
        story_id=story_id,
        name=name,
        role=role,
        profile_json=json.dumps(profile_json)
    )
    session.add(character)
    await session.commit()
    await session.refresh(character)
    logger.info(f"Created character: {character.name} (story_id={story_id})")
    return character


async def get_story_characters(
    session: AsyncSession,
    story_id: int
) -> List[Character]:
    """Get all characters for a story."""
    query = select(Character).where(Character.story_id == story_id)
    query = query.options(
        selectinload(Character.mentions),
        selectinload(Character.relationships_a),
        selectinload(Character.relationships_b)
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_character(
    session: AsyncSession,
    character_id: int
) -> Optional[Character]:
    """Get a character by ID with all relationships."""
    query = select(Character).where(Character.id == character_id)
    query = query.options(
        selectinload(Character.mentions),
        selectinload(Character.relationships_a).selectinload(CharacterRelationship.character_b),
        selectinload(Character.relationships_b).selectinload(CharacterRelationship.character_a)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def update_character(
    session: AsyncSession,
    character_id: int,
    name: Optional[str] = None,
    role: Optional[CharacterRole] = None,
    profile_json: Optional[Dict[str, Any]] = None
) -> Optional[Character]:
    """Update a character."""
    character = await session.get(Character, character_id)
    if not character:
        return None
    
    if name is not None:
        character.name = name
    if role is not None:
        character.role = role
    if profile_json is not None:
        character.profile_json = json.dumps(profile_json)
    
    await session.commit()
    await session.refresh(character)
    logger.info(f"Updated character: {character_id}")
    return character


async def delete_character(
    session: AsyncSession,
    character_id: int
) -> bool:
    """Delete a character and all related data."""
    character = await session.get(Character, character_id)
    if not character:
        return False
    
    await session.delete(character)
    await session.commit()
    logger.info(f"Deleted character: {character_id}")
    return True


# Character Mention CRUD
async def create_character_mention(
    session: AsyncSession,
    scene_id: int,
    character_id: int,
    context: str,
    mention_type: Optional[str] = None
) -> CharacterMention:
    """Create a character mention in a scene."""
    mention = CharacterMention(
        scene_id=scene_id,
        character_id=character_id,
        context=context,
        mention_type=mention_type
    )
    session.add(mention)
    await session.commit()
    await session.refresh(mention)
    return mention


async def get_character_mentions(
    session: AsyncSession,
    character_id: int
) -> List[CharacterMention]:
    """Get all mentions of a character."""
    query = select(CharacterMention).where(
        CharacterMention.character_id == character_id
    )
    query = query.options(selectinload(CharacterMention.scene))
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_scene_mentions(
    session: AsyncSession,
    scene_id: int
) -> List[CharacterMention]:
    """Get all character mentions in a scene."""
    query = select(CharacterMention).where(
        CharacterMention.scene_id == scene_id
    )
    query = query.options(selectinload(CharacterMention.character))
    result = await session.execute(query)
    return list(result.scalars().all())


# Character Relationship CRUD
async def create_relationship(
    session: AsyncSession,
    character_a_id: int,
    character_b_id: int,
    relationship_type: RelationshipType,
    strength: int = 5,
    notes: Optional[str] = None
) -> CharacterRelationship:
    """Create a relationship between two characters."""
    # Check if relationship already exists
    existing = await session.execute(
        select(CharacterRelationship).where(
            and_(
                CharacterRelationship.character_a_id == character_a_id,
                CharacterRelationship.character_b_id == character_b_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Relationship already exists")
    
    relationship = CharacterRelationship(
        character_a_id=character_a_id,
        character_b_id=character_b_id,
        type=relationship_type,
        strength=strength,
        notes=notes
    )
    session.add(relationship)
    await session.commit()
    await session.refresh(relationship)
    logger.info(f"Created relationship: {character_a_id} -> {character_b_id}")
    return relationship


async def get_character_relationships(
    session: AsyncSession,
    character_id: int
) -> List[CharacterRelationship]:
    """Get all relationships for a character."""
    query = select(CharacterRelationship).where(
        or_(
            CharacterRelationship.character_a_id == character_id,
            CharacterRelationship.character_b_id == character_id
        )
    )
    query = query.options(
        selectinload(CharacterRelationship.character_a),
        selectinload(CharacterRelationship.character_b)
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_relationship(
    session: AsyncSession,
    relationship_id: int,
    relationship_type: Optional[RelationshipType] = None,
    strength: Optional[int] = None,
    notes: Optional[str] = None
) -> Optional[CharacterRelationship]:
    """Update a relationship."""
    relationship = await session.get(CharacterRelationship, relationship_id)
    if not relationship:
        return None
    
    if relationship_type is not None:
        relationship.type = relationship_type
    if strength is not None:
        relationship.strength = strength
    if notes is not None:
        relationship.notes = notes
    
    await session.commit()
    await session.refresh(relationship)
    return relationship


async def delete_relationship(
    session: AsyncSession,
    relationship_id: int
) -> bool:
    """Delete a relationship."""
    relationship = await session.get(CharacterRelationship, relationship_id)
    if not relationship:
        return False
    
    await session.delete(relationship)
    await session.commit()
    logger.info(f"Deleted relationship: {relationship_id}")
    return True
