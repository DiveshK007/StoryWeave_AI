import json
import tempfile
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Depends, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from .settings import settings
from .retrieval import store
from .nim_client import call_llm
from .database import db
from .crud import (
    create_story, get_user_stories, get_story, update_scene,
    delete_project, create_project, get_project, StoryStatus,
    create_beat, get_story_beats, create_scene
)
from .models import Beat
from .logger import logger
from .sentry_config import (
    init_sentry, set_user_context, set_request_context,
    add_breadcrumb, capture_exception, start_transaction
)
from .exceptions import (
    StoryWeaveException, StoryGenerationError, LLMAPIError,
    RateLimitError, DatabaseConnectionError, VectorStoreError
)
from .admin import router as admin_router
from .character_router import router as character_router
from .collaboration_router import router as collaboration_router
from .analytics import (
    track_story_created, track_outline_generated, track_scene_expanded,
    track_story_exported, track_error_occurred, track_api_call,
    update_user_last_active
)

# Initialize FastAPI app
app = FastAPI(
    title='StoryWeave AI',
    description='RAG-based story generation tool',
    version='1.0.0'
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Sentry before other middleware
init_sentry()

# Middleware for Sentry context
class SentryContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set Sentry context for each request."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Set Sentry request context
        set_request_context(request_id=request_id)
        
        # Add breadcrumb for request
        add_breadcrumb(
            message=f"{request.method} {request.url.path}",
            category="http",
            level="info",
            data={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query)
            }
        )
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(SentryContextMiddleware)

# Include admin router
app.include_router(admin_router)

# Include character router
app.include_router(character_router)

# Include collaboration router
app.include_router(collaboration_router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Starting StoryWeave AI")
    add_breadcrumb(message="Application startup", category="lifecycle", level="info")
    
    try:
        # Initialize database
        await db.initialize()
        logger.info("Database initialized")
        add_breadcrumb(message="Database initialized", category="database", level="info")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        capture_exception(e, component="database", event="startup")
        # Raise exception if database is critical
        raise
    
    try:
        if store.load_index():
            logger.info(f"Loaded existing index with {len(store.chunks)} chunks")
            add_breadcrumb(
                message=f"Loaded index with {len(store.chunks)} chunks",
                category="vector_store",
                level="info"
            )
    except Exception as e:
        logger.warning(f"Could not load existing index: {e}")
        add_breadcrumb(
            message=f"Failed to load index: {str(e)}",
            category="vector_store",
            level="warning"
        )
    
    # Start background tasks for collaboration
    try:
        from .collaboration_websocket import lock_cleanup_task
        import asyncio
        asyncio.create_task(lock_cleanup_task())
        logger.info("Started collaboration lock cleanup task")
    except Exception as e:
        logger.warning(f"Could not start lock cleanup task: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    add_breadcrumb(message="Application shutdown", category="lifecycle", level="info")
    await db.close()
    logger.info("StoryWeave AI shutdown complete")

# Exception handlers
@app.exception_handler(StoryWeaveException)
async def storyweave_exception_handler(request: Request, exc: StoryWeaveException):
    """Handle custom StoryWeave exceptions."""
    exc.capture_to_sentry()
    return exc.to_http_exception()

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    # Get request context
    request_id = getattr(request.state, "request_id", None)
    set_request_context(request_id=request_id)
    
    # Capture to Sentry
    capture_exception(
        exc,
        endpoint=request.url.path,
        method=request.method,
        request_id=request_id
    )
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "request_id": request_id
        }
    )


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        index_status = "ready" if store.index is not None else "not_ready"
        db_status = await db.health_check()
        
        return {
            "status": "healthy" if db_status else "degraded",
            "version": "1.0.0",
            "index_status": index_status,
            "chunks_count": len(store.chunks) if store.index else 0,
            "database_status": "connected" if db_status else "disconnected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )


# Request/Response models with validation
class OutlineReq(BaseModel):
    premise: str = Field(..., min_length=10, max_length=500, description="Story premise")
    genre: str = Field(default='sci-fi', max_length=50, description="Story genre")
    length: str = Field(default='short', pattern='^(short|feature|long)$', description="Story length")
    style: Optional[str] = Field(default=None, max_length=200, description="Writing style")
    
    @field_validator('premise')
    @classmethod
    def validate_premise(cls, v):
        if not v or not v.strip():
            raise ValueError('Premise cannot be empty')
        return v.strip()


class SceneReq(BaseModel):
    outline: Dict[str, Any] = Field(..., description="Story outline")
    scene_index: int = Field(..., ge=0, description="Index of scene to expand")
    protagonist: Optional[str] = Field(default=None, max_length=100, description="Protagonist name")
    style: Optional[str] = Field(default=None, max_length=200, description="Writing style")


class ExportReq(BaseModel):
    outline: Dict[str, Any] = Field(..., description="Story outline")
    scenes: List[str] = Field(default_factory=list, description="List of scene texts")
    save_to_db: bool = Field(default=False, description="Save story to database")


# Validation functions
def check_beats_consistency(outline_json: dict) -> dict:
    """Check if outline beats are consistent."""
    issues = []
    beats = outline_json.get('beats', [])
    
    if len(beats) < 5:
        issues.append('Outline has fewer than 5 beats.')
    
    if len(beats) > 10:
        issues.append('Outline has more than 10 beats (may be too long).')
    
    titles = [b.get('title', '').lower() for b in beats]
    if not any('inciting' in t for t in titles):
        issues.append('Missing inciting incident.')
    
    # Check for required fields in beats
    for i, beat in enumerate(beats):
        if not beat.get('title'):
            issues.append(f'Beat {i+1} is missing a title.')
    
    return {'ok': len(issues) == 0, 'issues': issues}


def check_continuity(prev_scenes: list, new_scene: dict) -> dict:
    """Check continuity between scenes."""
    names = []
    for sc in prev_scenes:
        n = sc.get('protagonist')
        if n:
            names.append(n)
    
    expected = names[0] if names else None
    if expected and new_scene.get('protagonist') and new_scene['protagonist'] != expected:
        return {
            'ok': False,
            'issue': f'Protagonist changed from {expected} to {new_scene["protagonist"]}'
        }
    return {'ok': True}


# API Endpoints
@app.post('/ingest')
async def ingest(files: List[UploadFile] = File(...)):
    """
    Ingest documents into the vector store.
    
    Validates file types, sizes, and handles errors gracefully.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    if len(files) > settings.MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum is {settings.MAX_UPLOAD_FILES}"
        )
    
    temp_paths = []
    source_names = []
    
    try:
        for file in files:
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in list(settings.ALLOWED_EXTENSIONS):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file_ext} not allowed. Allowed: {list(settings.ALLOWED_EXTENSIONS)}"
                )
            
            # Read file content
            content = await file.read()
            
            # Validate file size
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} exceeds maximum size of {settings.MAX_FILE_SIZE} bytes"
                )
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_ext,
                dir=settings.UPLOAD_DIR
            )
            temp_file.write(content)
            temp_file.close()
            
            temp_paths.append(temp_file.name)
            source_names.append(file.filename)
            
            logger.info(f"Saved uploaded file: {file.filename} ({len(content)} bytes)")
        
        # Ingest documents
        store.ingest_docs(temp_paths, settings.EMBED_URL, source_names)
        
        return {
            'ok': True,
            'chunks': len(store.chunks),
            'files_processed': len(temp_paths)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ingest: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest files: {str(e)}"
        )
    finally:
        # Cleanup temporary files
        for path in temp_paths:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {path}: {e}")


@app.get('/ask')
async def ask(q: str):
    """
    Ask a question using RAG.
    
    Args:
        q: Question to ask
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )
    
    if not store.index:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No index available. Please upload documents via /ingest first"
        )
    
    try:
        hits = store.search(q, settings.EMBED_URL, settings.TOP_K)
        
        if not hits:
            return {'answer': 'No relevant context found.', 'matches': []}
        
        # Get context from chunks
        ctx = '\n\n'.join([store.chunks[i] for i, _ in hits])
        
        prompt = (
            'Use the context to answer precisely. Cite key facts. '
            '\n\nContext:\n' + ctx + '\n\nQuestion: ' + q + '\nAnswer:'
        )
        
        text = await call_llm(prompt, settings.LLM_URL, settings.MAX_TOKENS)
        
        return {'answer': text, 'matches': hits}
        
    except ValueError as e:
        logger.error(f"Error in ask endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM call failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in ask: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.post('/generate_outline')
async def generate_outline(req: OutlineReq):
    """
    Generate a story outline from a premise.
    
    Uses RAG to find relevant story beats and generates an outline.
    """
    try:
        # Search for relevant context
        hits = []
        if store.index:
            query = f"{req.genre} story beats {req.premise}"
            hits = store.search(query, settings.EMBED_URL, settings.TOP_K)
        
        ctx = '\n\n'.join([store.chunks[i] for i, _ in hits]) if hits else ''
        
        # Build prompt
        prompt = (
            f"You are a story planner. Premise: {req.premise}\n"
            f"Genre: {req.genre}\n"
            f"Length: {req.length}\n"
        )
        
        if req.style:
            prompt += f"Style: {req.style}\n"
        
        prompt += (
            f"Context:\n{ctx}\n"
            "Return JSON with keys logline and beats (7 items max). "
            "Each beat: title, goal, conflict, outcome."
        )
        
        # Call LLM
        text = await call_llm(prompt, settings.LLM_URL, 550)
        
        # Parse JSON response
        try:
            outline = json.loads(text)
            # Validate structure
            if not isinstance(outline, dict):
                raise ValueError("Outline is not a dictionary")
            if 'beats' not in outline:
                outline['beats'] = []
            if 'logline' not in outline:
                outline['logline'] = req.premise
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Fallback outline
            outline = {
                'logline': req.premise,
                'beats': [{'title': 'Hook', 'goal': '', 'conflict': '', 'outcome': ''}]
            }
        
        # Check consistency
        check = check_beats_consistency(outline)
        
        return {
            'outline': outline,
            'consistency': check,
            'matches': hits
        }
        
    except ValueError as e:
        logger.error(f"Error in generate_outline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate outline: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in generate_outline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.post('/expand_scene')
async def expand_scene(req: SceneReq):
    """
    Expand a story beat into a full scene.
    
    Args:
        req: Scene request with outline, scene_index, and optional style/protagonist
    """
    try:
        beats = req.outline.get('beats', [])
        
        if not beats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Outline has no beats"
            )
        
        # Validate and clamp scene index
        idx = max(0, min(req.scene_index, len(beats) - 1))
        if idx != req.scene_index:
            logger.warning(f"Scene index {req.scene_index} clamped to {idx}")
        
        beat = beats[idx] if beats else {'title': 'Scene', 'goal': '', 'conflict': '', 'outcome': ''}
        
        # Check continuity (simplified - in production, track previous scenes)
        prev = []
        continuity = check_continuity(prev, {'protagonist': req.protagonist or ''})
        
        # Build prompt
        prompt = (
            f"Expand the following beat into a cinematic scene.\n"
            f"Beat: {beat}\n"
        )
        
        if req.protagonist:
            prompt += f"Protagonist: {req.protagonist}\n"
        
        prompt += (
            f"Style: {req.style or 'visceral, visual, concise action lines'}\n"
            "Write 10-15 sentences with clear start-middle-end. "
            "End with a one-line cliffhanger."
        )
        
        # Call LLM
        text = await call_llm(prompt, settings.LLM_URL, 700)
        
        return {
            'scene_text': text,
            'continuity': continuity,
            'scene_index': idx
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error in expand_scene: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to expand scene: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in expand_scene: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.post("/export", response_class=PlainTextResponse)
async def export_story(req: ExportReq):
    """
    Export story as text file.
    
    Expects: {"outline": {...}, "scenes": ["...", "..."], "save_to_db": bool}
    Returns: text/plain with download headers.
    """
    try:
        outline = req.outline or {}
        scenes = req.scenes or []
        
        # Build export text
        text = "# " + outline.get("logline", "Untitled") + "\n\n"
        
        # Add beats section
        for i, beat in enumerate(outline.get("beats", []), 1):
            title = beat.get("title", f"Scene {i}")
            text += f"## {title}\n"
            text += f"Goal: {beat.get('goal', '')}\n"
            text += f"Conflict: {beat.get('conflict', '')}\n"
            text += f"Outcome: {beat.get('outcome', '')}\n\n"
            
            # Add corresponding scene if available
            if i - 1 < len(scenes) and scenes[i - 1]:
                text += scenes[i - 1] + "\n\n"
        
        text = text.strip() or "Empty story."
        
        # Save to database if requested
        # Note: This requires a project_id and user_id - for now, we'll skip saving
        # In production, you'd extract these from authentication context
        if req.save_to_db:
            logger.warning("save_to_db is requested but requires project_id and user_id. Skipping save.")
            # TODO: Implement proper user authentication and project context
            # async with db.get_session() as session:
            #     story = await create_story(
            #         session=session,
            #         project_id=project_id,
            #         premise=outline.get("logline", ""),
            #         genre=outline.get("genre"),
            #         length=outline.get("length"),
            #         logline=outline.get("logline"),
            #         beats_data=outline.get("beats", [])
            #     )
        
        # Generate filename
        logline = outline.get("logline", "Untitled")
        safe_filename = "".join(c for c in logline[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_filename = safe_filename.replace(' ', '_') or "story"
        
        headers = {
            "Content-Disposition": f'attachment; filename="{safe_filename}.txt"'
        }
        
        return PlainTextResponse(text, headers=headers, media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error in export_story: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export story: {str(e)}"
        )


# Story management endpoints
@app.get("/stories")
def list_stories(limit: int = 50, offset: int = 0):
    """List saved stories."""
    try:
        stories = db.list_stories(limit=limit, offset=offset)
        return {
            "stories": [
                {
                    "id": s.id,
                    "title": s.title,
                    "logline": s.logline,
                    "genre": s.genre,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in stories
            ],
            "count": len(stories)
        }
    except Exception as e:
        logger.error(f"Error listing stories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list stories"
        )


@app.get("/stories/{story_id}")
def get_story(story_id: int):
    """Get a story by ID."""
    try:
        story = db.get_story(story_id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Story {story_id} not found"
            )
        
        return {
            "id": story.id,
            "title": story.title,
            "logline": story.logline,
            "premise": story.premise,
            "genre": story.genre,
            "outline": story.outline,
            "scenes": story.scenes,
            "created_at": story.created_at.isoformat() if story.created_at else None,
            "updated_at": story.updated_at.isoformat() if story.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting story: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get story"
        )


# Beat management endpoints
@app.get("/stories/{story_id}/beats")
async def get_story_beats_endpoint(
    story_id: int,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Get all beats for a story."""
    try:
        beats = await get_story_beats(session=session, story_id=story_id)
        return {
            "beats": [
                {
                    "id": b.id,
                    "beat_index": b.beat_index,
                    "title": b.title,
                    "goal": b.goal,
                    "conflict": b.conflict,
                    "outcome": b.outcome,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                    "updated_at": b.updated_at.isoformat() if b.updated_at else None
                }
                for b in beats
            ]
        }
    except Exception as e:
        logger.error(f"Error getting beats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get beats"
        )


class BeatUpdateReq(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    goal: Optional[str] = None
    conflict: Optional[str] = None
    outcome: Optional[str] = None
    beat_index: Optional[int] = Field(None, ge=0)


@app.put("/beats/{beat_id}")
async def update_beat(
    beat_id: int,
    req: BeatUpdateReq,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Update a beat."""
    try:
        beat = await session.get(Beat, beat_id)
        if not beat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Beat {beat_id} not found"
            )
        
        if req.title is not None:
            beat.title = req.title
        if req.goal is not None:
            beat.goal = req.goal
        if req.conflict is not None:
            beat.conflict = req.conflict
        if req.outcome is not None:
            beat.outcome = req.outcome
        if req.beat_index is not None:
            beat.beat_index = req.beat_index
        
        await session.commit()
        await session.refresh(beat)
        
        return {
            "id": beat.id,
            "beat_index": beat.beat_index,
            "title": beat.title,
            "goal": beat.goal,
            "conflict": beat.conflict,
            "outcome": beat.outcome
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating beat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update beat"
        )


@app.delete("/beats/{beat_id}")
async def delete_beat(
    beat_id: int,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Delete a beat."""
    try:
        beat = await session.get(Beat, beat_id)
        if not beat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Beat {beat_id} not found"
            )
        
        await session.delete(beat)
        await session.commit()
        
        return {"ok": True, "message": f"Beat {beat_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting beat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete beat"
        )


class BeatReorderReq(BaseModel):
    beat_ids: List[int] = Field(..., description="List of beat IDs in new order")


@app.post("/stories/{story_id}/beats/reorder")
async def reorder_beats(
    story_id: int,
    req: BeatReorderReq,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Reorder beats by updating their beat_index values."""
    try:
        # Get all beats for the story
        beats = await get_story_beats(session=session, story_id=story_id)
        beat_dict = {b.id: b for b in beats}
        
        # Update beat_index for each beat in the new order
        for new_index, beat_id in enumerate(req.beat_ids):
            if beat_id in beat_dict:
                beat_dict[beat_id].beat_index = new_index
        
        await session.commit()
        
        # Return updated beats
        updated_beats = await get_story_beats(session=session, story_id=story_id)
        return {
            "beats": [
                {
                    "id": b.id,
                    "beat_index": b.beat_index,
                    "title": b.title,
                    "goal": b.goal,
                    "conflict": b.conflict,
                    "outcome": b.outcome
                }
                for b in updated_beats
            ]
        }
    except Exception as e:
        logger.error(f"Error reordering beats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder beats"
        )


@app.post("/stories/{story_id}/beats")
async def create_beat_endpoint(
    story_id: int,
    req: BeatUpdateReq,
    session: AsyncSession = Depends(db.get_db_session)
):
    """Create a new beat for a story."""
    try:
        # Get current max beat_index
        beats = await get_story_beats(session=session, story_id=story_id)
        max_index = max([b.beat_index for b in beats], default=-1)
        
        beat = await create_beat(
            session=session,
            story_id=story_id,
            beat_index=max_index + 1,
            title=req.title or "New Beat",
            goal=req.goal,
            conflict=req.conflict,
            outcome=req.outcome
        )
        
        return {
            "id": beat.id,
            "beat_index": beat.beat_index,
            "title": beat.title,
            "goal": beat.goal,
            "conflict": beat.conflict,
            "outcome": beat.outcome
        }
    except Exception as e:
        logger.error(f"Error creating beat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create beat"
        )


# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
