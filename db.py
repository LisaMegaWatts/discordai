import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ai_ide_user:ai_ide_password@localhost:5432/ai_ide_db")
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    future=True
)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# AsyncSession factory/context manager for per-coroutine usage.
# Usage pattern: Each async task/coroutine should create its own session using:
#   async with AsyncSessionLocal() as session:
#       ... # use session here
# Do NOT share session objects between coroutines/tasks.

async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session

Base = declarative_base()
__all__ = ["engine", "AsyncSessionLocal", "Base"]

# Proper shutdown for async engine
async def shutdown_async_db():
    # Dispose engine before event loop termination
    await engine.dispose()