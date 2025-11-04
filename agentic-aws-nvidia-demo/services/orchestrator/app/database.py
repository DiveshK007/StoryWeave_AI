"""
Database connection and session management for StoryWeave AI.

Uses async SQLAlchemy with PostgreSQL (asyncpg) and SQLite (aiosqlite) fallback.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, text
from .models import Base
from .settings import settings
from .logger import logger


class Database:
    """Database manager with async SQLAlchemy."""
    
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[async_sessionmaker] = None
        self._initialized = False
    
    def _get_database_url(self) -> str:
        """Get the database URL, converting sync to async if needed."""
        db_url = settings.DATABASE_URL
        
        # Convert SQLite to async SQLite
        if db_url.startswith("sqlite:///"):
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        # Convert PostgreSQL to async PostgreSQL
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        elif db_url.startswith("postgresql+psycopg2://"):
            db_url = db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        
        return db_url
    
    def _get_pool_class(self):
        """Get the appropriate connection pool class based on database type."""
        db_url = settings.DATABASE_URL
        # SQLite doesn't support connection pooling well
        if "sqlite" in db_url:
            return NullPool
        # PostgreSQL uses connection pooling
        return QueuePool
    
    async def initialize(self):
        """Initialize the database connection and create tables if needed."""
        if self._initialized:
            return
        
        try:
            db_url = self._get_database_url()
            pool_class = self._get_pool_class()
            
            # Configure engine with connection pooling for production
            connect_args = {}
            if "sqlite" in db_url:
                connect_args = {"check_same_thread": False}
            
            # Create async engine
            pool_kwargs = {
                "pool_pre_ping": True,  # Verify connections before using
            }
            
            # Add connection pool settings for PostgreSQL
            if "postgresql" in db_url:
                pool_kwargs["pool_size"] = settings.DB_POOL_SIZE
                pool_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
            
            self.engine = create_async_engine(
                db_url,
                echo=settings.ENVIRONMENT == "development",  # Log SQL in dev
                poolclass=pool_class,
                connect_args=connect_args,
                **pool_kwargs
            )
            
            # Create async session factory
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )
            
            # Create tables in development
            if settings.ENVIRONMENT == "development":
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created (development mode)")
            
            self._initialized = True
            logger.info(f"Database initialized: {db_url.split('@')[-1] if '@' in db_url else db_url}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session context manager.
        
        Usage:
            async with db.get_session() as session:
                # Use session
                pass
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        FastAPI dependency for getting database sessions.
        
        Usage in FastAPI:
            @app.get("/endpoint")
            async def endpoint(session: AsyncSession = Depends(db.get_db_session)):
                # Use session
                pass
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance
db = Database()
