"""
Character management API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .database import db
from .character_crud import (
    create_character, get_story_characters, get_character,
    update_character, delete_character,
    get_character_mentions, create_character_mention,
    create_relationship, get_character_relationships
)
from .character_service import (
    generate_character_profile,
    analyze_character_consistency,
    extract_character_mentions
)
from .models import CharacterRole, RelationshipType
from .crud import get_story, get_beat_scenes
from .logger import logger
import json

router = APIRouter(prefix="/characters", tags=["characters"])


# Request/Response Models
class CharacterGenerateReq(BaseModel):
    story_id: int
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern="^(protagonist|antagonist|supporting|minor)$")


class CharacterUpdateReq(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, pattern="^(protagonist|antagonist|supporting|minor)$")
    profile_json: Optional[Dict[str, Any]] = None


class RelationshipCreateReq(BaseModel):
    character_a_id: int
    character_b_id: int
    type: str = Field(..., pattern="^(family|friend|enemy|romance|mentor|rival|ally|other)$")
    strength: int = Field(5, ge=1, le=10)
    notes: Optional[str] = None


@router.post("/generate")
async def generate_character(
    req: CharacterGenerateReq,
    session: AsyncSession = Depends(db.get_db_session)
):
    """
    Generate a character profile using AI.
    
    Creates a new character with AI-generated profile.
    """
    try:
        # Get story for context
        story = await get_story(session=session, story_id=req.story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Story {req.story_id} not found"
            )
        
        # Generate character profile
        profile = await generate_character_profile(
            name=req.name,
            role=req.role,
            story_premise=story.premise,
            genre=story.genre
        )
        
        # Create character
        character_role = CharacterRole[req.role.upper()]
        character = await create_character(
            session=session,
            story_id=req.story_id,
            name=req.name,
            role=character_role,
            profile_json=profile
        )
        
        return {
            "id": character.id,
            "name": character.name,
            "role": character.role.value,
            "profile": json.loads(character.profile_json)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating character: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate character: {str(e)}"
        )


@router.get("/stories/{story_id}/characters")
async def get_characters_for_story(
    story_id: int,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Get all characters for a story."""
    try:
        characters = await get_story_characters(session=session, story_id=story_id)
        
        return {
            "characters": [
                {
                    "id": char.id,
                    "name": char.name,
                    "role": char.role.value,
                    "profile": json.loads(char.profile_json),
                    "created_at": char.created_at.isoformat()
                }
                for char in characters
            ]
        }
    except Exception as e:
        logger.error(f"Error getting characters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get characters"
        )


@router.get("/{character_id}")
async def get_character_detail(
    character_id: int,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Get character details with relationships and mentions."""
    try:
        character = await get_character(session=session, character_id=character_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {character_id} not found"
            )
        
        # Get relationships
        relationships = await get_character_relationships(
            session=session,
            character_id=character_id
        )
        
        # Format relationships
        rel_data = []
        for rel in relationships:
            other_char = rel.character_b if rel.character_a_id == character_id else rel.character_a
            rel_data.append({
                "id": rel.id,
                "character_id": other_char.id,
                "character_name": other_char.name,
                "type": rel.type.value,
                "strength": rel.strength,
                "notes": rel.notes
            })
        
        return {
            "id": character.id,
            "name": character.name,
            "role": character.role.value,
            "profile": json.loads(character.profile_json),
            "relationships": rel_data,
            "mention_count": len(character.mentions),
            "created_at": character.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting character: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get character"
        )


@router.post("/{character_id}/analyze-consistency")
async def analyze_consistency(
    character_id: int,
    session: AsyncSession = Depends(db.get_db_session)
):
    """
    Analyze character consistency across all scenes in the story.
    
    Scans all scenes for character mentions and checks for inconsistencies.
    """
    try:
        character = await get_character(session=session, character_id=character_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {character_id} not found"
            )
        
        # Get all scenes from the story
        story = await get_story(session=session, story_id=character.story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Story {character.story_id} not found"
            )
        
        # Collect all scene texts
        scene_texts = []
        for beat in story.beats:
            scenes = await get_beat_scenes(session=session, beat_id=beat.id, latest_only=True)
            for scene in scenes:
                scene_texts.append(scene.text)
        
        if not scene_texts:
            return {
                "character_id": character_id,
                "character_name": character.name,
                "consistent": True,
                "issues": [],
                "mentions": [],
                "message": "No scenes found to analyze"
            }
        
        # Analyze consistency
        profile = json.loads(character.profile_json)
        analysis = await analyze_character_consistency(
            character_name=character.name,
            character_profile=profile,
            scene_texts=scene_texts
        )
        
        return {
            "character_id": character_id,
            "character_name": character.name,
            **analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing consistency: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze consistency: {str(e)}"
        )


@router.get("/{character_id}/mentions")
async def get_mentions(
    character_id: int,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Get all mentions of a character across scenes."""
    try:
        mentions = await get_character_mentions(session=session, character_id=character_id)
        
        return {
            "character_id": character_id,
            "mentions": [
                {
                    "id": mention.id,
                    "scene_id": mention.scene_id,
                    "context": mention.context,
                    "mention_type": mention.mention_type,
                    "created_at": mention.created_at.isoformat()
                }
                for mention in mentions
            ]
        }
    except Exception as e:
        logger.error(f"Error getting mentions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get mentions"
        )


@router.put("/{character_id}")
async def update_character_endpoint(
    character_id: int,
    req: CharacterUpdateReq,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Update a character."""
    try:
        role = None
        if req.role:
            role = CharacterRole[req.role.upper()]
        
        character = await update_character(
            session=session,
            character_id=character_id,
            name=req.name,
            role=role,
            profile_json=req.profile_json
        )
        
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {character_id} not found"
            )
        
        return {
            "id": character.id,
            "name": character.name,
            "role": character.role.value,
            "profile": json.loads(character.profile_json)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating character: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update character"
        )


@router.delete("/{character_id}")
async def delete_character_endpoint(
    character_id: int,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Delete a character."""
    try:
        success = await delete_character(session=session, character_id=character_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character {character_id} not found"
            )
        
        return {"success": True, "message": f"Character {character_id} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting character: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete character"
        )


@router.post("/relationships")
async def create_relationship_endpoint(
    req: RelationshipCreateReq,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Create a relationship between two characters."""
    try:
        rel_type = RelationshipType[req.type.upper()]
        
        relationship = await create_relationship(
            session=session,
            character_a_id=req.character_a_id,
            character_b_id=req.character_b_id,
            relationship_type=rel_type,
            strength=req.strength,
            notes=req.notes
        )
        
        return {
            "id": relationship.id,
            "character_a_id": relationship.character_a_id,
            "character_b_id": relationship.character_b_id,
            "type": relationship.type.value,
            "strength": relationship.strength,
            "notes": relationship.notes
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating relationship: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create relationship"
        )
