import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.database.models import Base, Achievement
from app.core.constants import ACHIEVEMENT_DEFINITIONS

logger = logging.getLogger(__name__)

# Normalize database URL
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True if not db_url.startswith("sqlite") else False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initializes database schema and populates default achievements."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Populate achievements if missing
        async with AsyncSessionLocal() as session:
            for ach in ACHIEVEMENT_DEFINITIONS:
                existing = await session.get(Achievement, ach["id"])
                if not existing:
                    new_ach = Achievement(
                        id=ach["id"],
                        name=ach["name"],
                        icon=ach["icon"],
                        description=ach["desc"],
                        xp_reward=50
                    )
                    session.add(new_ach)
            await session.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(f"CRITICAL: Production PostgreSQL initialization failed: {e}") from e
        raise e
