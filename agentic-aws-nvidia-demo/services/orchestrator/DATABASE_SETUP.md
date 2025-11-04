# Database Setup Guide

This document describes the database persistence setup for StoryWeave AI.

## Overview

The application uses async SQLAlchemy with:
- **PostgreSQL** (production) with `asyncpg` driver
- **SQLite** (development) with `aiosqlite` driver

## Environment Configuration

Set the `DATABASE_URL` environment variable:

```bash
# For SQLite (development)
export DATABASE_URL="sqlite:///./storyweave.db"

# For PostgreSQL (production)
export DATABASE_URL="postgresql://user:password@localhost:5432/storyweave"
```

Or create a `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost:5432/storyweave
```

## Database Models

The following models are defined in `app/models.py`:

- **User**: User accounts with email and password hash
- **Project**: Projects owned by users for organizing stories
- **Story**: Stories with premise, genre, logline, and status
- **Beat**: Story structure beats with goal, conflict, outcome
- **Scene**: Scene text with versioning support
- **CorpusDocument**: Reference documents for projects

All models inherit from `BaseModel` with `id`, `created_at`, and `updated_at` fields.

## Database Migrations

Alembic is configured for database versioning.

### Initial Setup

1. Create the initial migration:
```bash
cd agentic-aws-nvidia-demo/services/orchestrator
alembic revision --autogenerate -m "Initial migration"
```

2. Apply migrations:
```bash
alembic upgrade head
```

### Creating New Migrations

After changing models:
```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Rolling Back

```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

## Usage Examples

### In FastAPI Endpoints

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import db
from .crud import create_story, get_user_stories

@app.post("/stories")
async def create_story_endpoint(
    session: AsyncSession = Depends(db.get_db_session)
):
    story = await create_story(
        session=session,
        project_id=1,
        premise="A story about...",
        genre="sci-fi"
    )
    return {"id": story.id}
```

### Direct Session Usage

```python
from .database import db
from .crud import create_project

async with db.get_session() as session:
    project = await create_project(
        session=session,
        user_id=1,
        name="My Project"
    )
```

## CRUD Operations

All CRUD operations are in `app/crud.py`:

- **User**: `create_user`, `get_user_by_email`, `get_user_by_id`
- **Project**: `create_project`, `get_user_projects`, `get_project`, `delete_project`
- **Story**: `create_story`, `get_user_stories`, `get_story`, `update_story`
- **Beat**: `create_beat`, `get_story_beats`
- **Scene**: `create_scene`, `update_scene`, `get_beat_scenes`
- **CorpusDocument**: `create_corpus_document`, `get_project_corpus_documents`

## Connection Pooling

For PostgreSQL, connection pooling is configured:
- `DB_POOL_SIZE`: 10 (default)
- `DB_MAX_OVERFLOW`: 20 (default)

These can be set in `settings.py` or via environment variables.

## Development vs Production

- **Development**: Tables are auto-created on startup (SQLite)
- **Production**: Use Alembic migrations (PostgreSQL)

Set `ENVIRONMENT=production` to disable auto-creation.

