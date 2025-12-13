import os
import threading
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

# Global registry for tracking AsyncSession and AsyncEngine objects
class AsyncDBRegistry:
    def __init__(self):
        self._sessions = set()
        self._engines = set()
        self._lock = threading.Lock()
        self.logger = logging.getLogger("AsyncDBRegistry")

    def register_session(self, session):
        with self._lock:
            self._sessions.add(session)
            self.logger.info(f"[REGISTRY] Registered AsyncSession: {id(session)}")

    def deregister_session(self, session):
        with self._lock:
            self._sessions.discard(session)
            self.logger.info(f"[REGISTRY] Deregistered AsyncSession: {id(session)}")

    def register_engine(self, engine):
        with self._lock:
            self._engines.add(engine)
            self.logger.info(f"[REGISTRY] Registered AsyncEngine: {id(engine)}")

    def deregister_engine(self, engine):
        with self._lock:
            self._engines.discard(engine)
            self.logger.info(f"[REGISTRY] Deregistered AsyncEngine: {id(engine)}")

    def get_sessions(self):
        with self._lock:
            return list(self._sessions)

    def get_engines(self):
        with self._lock:
            return list(self._engines)

    def clear(self):
        with self._lock:
            self._sessions.clear()
            self._engines.clear()
            self.logger.info("[REGISTRY] Cleared all tracked sessions and engines.")

db_registry = AsyncDBRegistry()

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
db_registry.register_engine(engine)

class TrackedAsyncSession(AsyncSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        db_registry.register_session(self)

    async def close(self):
        db_registry.deregister_session(self)
        await super().close()

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=TrackedAsyncSession
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
    import asyncio
    logger = logging.getLogger("AsyncDBRegistry")
    def is_event_loop_closed():
        try:
            loop = asyncio.get_running_loop()
            return loop.is_closed()
        except RuntimeError:
            return True
    if is_event_loop_closed():
        logger.warning("[DIAG] Attempted DB engine dispose after event loop closed. Skipping DB cleanup.")
        return

    # Explicitly close all tracked AsyncSession objects
    sessions = db_registry.get_sessions()
    if sessions:
        logger.info(f"Closing {len(sessions)} tracked AsyncSession objects before engine disposal...")
        close_tasks = []
        for session in sessions:
            try:
                close_tasks.append(session.close())
            except Exception as e:
                logger.warning(f"Error closing AsyncSession: {e}")
        if close_tasks:
            try:
                await asyncio.gather(*close_tasks, return_exceptions=True)
                logger.info("AsyncSession objects closed and awaited successfully.")
            except Exception as e:
                logger.warning(f"Exception during AsyncSession close: {e}")

    # Dispose all tracked engines
    engines = db_registry.get_engines()
    if engines:
        logger.info(f"Disposing {len(engines)} tracked AsyncEngine objects...")
        for eng in engines:
            try:
                await eng.dispose()
                logger.info(f"AsyncEngine disposed: {id(eng)}")
                db_registry.deregister_engine(eng)
            except Exception as e:
                logger.error(f"Error disposing engine: {e}")

    # Dereference sessionmaker
    global AsyncSessionLocal
    AsyncSessionLocal = None
    logger.info("AsyncSessionLocal dereferenced.")

    db_registry.clear()

    # Diagnostic: confirm all tracked objects are finalized
    if not db_registry.get_engines() and not db_registry.get_sessions():
        logger.info("No lingering AsyncEngine or AsyncSession objects remain in registry.")
    else:
        logger.warning(f"Lingering AsyncEngine objects: {len(db_registry.get_engines())}; AsyncSession objects: {len(db_registry.get_sessions())}")