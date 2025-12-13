# shutdown_bot.py

import asyncio
import logging
import sys

from discord_bot import bot  # Assumes bot is imported from discord_bot.py
import db  # Import db module to allow global reference cleanup
from db import db_registry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SHUTDOWN] %(levelname)s: %(message)s"
)
logger = logging.getLogger("shutdown_bot")

async def shutdown_discord_bot():
    if bot.is_closed():
        logger.info("Discord bot is already stopped.")
        return
    logger.info("Stopping Discord bot...")
    try:
        await bot.close()
        logger.info("Discord bot stopped.")
    except Exception as e:
        logger.error(f"[DIAG] Exception during bot.close(): {e}")

async def cancel_background_tasks():
    logger.info("Cancelling all background tasks...")
    # Only cancel tasks that are not done and not the current task
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
    for task in tasks:
        task.cancel()
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("[DIAG] Background tasks cancelled and awaited successfully.")
    except Exception as e:
        logger.error(f"[DIAG] Exception during background task cancellation: {e}")
    logger.info("All background tasks cancelled.")

async def dispose_db():
    logger.info("Disposing SQLAlchemy engine and cleaning up AsyncSession objects...")

    # Check if event loop is closed before proceeding
    import asyncio
    def is_event_loop_closed():
        try:
            loop = asyncio.get_running_loop()
            return loop.is_closed()
        except RuntimeError:
            return True

    if is_event_loop_closed():
        logger.warning("[DIAG] Attempted DB engine dispose after event loop closed. Skipping DB cleanup.")
        return

    # Defensive: Await and close all AsyncSession objects before disposing engine
    import gc
    session_objs = []
    for obj in gc.get_objects():
        try:
            if type(obj).__name__ == "AsyncSession":
                session_objs.append(obj)
        except Exception:
            continue
    if session_objs:
        logger.info(f"Closing {len(session_objs)} AsyncSession objects before engine disposal...")
        close_tasks = []
        for session in session_objs:
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

    # Properly dispose engine and clean up global references
    try:
        if getattr(db, "engine", None):
            await db.engine.dispose()
            logger.info("AsyncEngine disposed.")
            db.engine = None
    except Exception as e:
        logger.error(f"Error disposing engine: {e}")

    # Remove AsyncSessionLocal global reference
    try:
        if hasattr(db, "AsyncSessionLocal"):
            db.AsyncSessionLocal = None
            logger.info("AsyncSessionLocal dereferenced.")
    except Exception as e:
        logger.error(f"Error dereferencing AsyncSessionLocal: {e}")

    # Final cleanup: Remove lingering AsyncEngine references
    import sys, ctypes
    gc.collect()
    logger.info("Garbage collection complete. Checking for lingering AsyncEngine/AsyncSession objects...")

    found_engines = []
    found_sessions = []
    engine_ids = []
    session_ids = []

    for obj in gc.get_objects():
        try:
            if obj.__class__.__name__ == "AsyncEngine":
                found_engines.append(obj)
                engine_ids.append(id(obj))
            if obj.__class__.__name__ == "AsyncSession":
                found_sessions.append(obj)
                session_ids.append(id(obj))
        except Exception:
            continue

    logger.info(f"AsyncEngine object IDs: {engine_ids}")
    logger.info(f"AsyncSession object IDs: {session_ids}")

    # Print reference counts for diagnostic purposes
    for eid in engine_ids:
        try:
            logger.info(f"Refcount for AsyncEngine id={eid}: {sys.getrefcount(ctypes.cast(eid, ctypes.py_object)) if hasattr(sys, 'getrefcount') else 'N/A'}")
        except Exception as e:
            logger.info(f"Error getting refcount for AsyncEngine id={eid}: {e}")
    for sid in session_ids:
        try:
            logger.info(f"Refcount for AsyncSession id={sid}: {sys.getrefcount(ctypes.cast(sid, ctypes.py_object)) if hasattr(sys, 'getrefcount') else 'N/A'}")
        except Exception as e:
            logger.info(f"Error getting refcount for AsyncSession id={sid}: {e}")

    if not found_engines and not found_sessions:
        logger.info("No lingering AsyncEngine or AsyncSession objects remain.")
    else:
        logger.warning(f"Lingering AsyncEngine objects: {len(found_engines)}; AsyncSession objects: {len(found_sessions)}")
async def main():
    logger.info("Shutdown sequence initiated.")
    try:
        await shutdown_discord_bot()
    except Exception as e:
        logger.error(f"Error stopping Discord bot: {e}")

    try:
        await cancel_background_tasks()
    except Exception as e:
        logger.error(f"Error cancelling background tasks: {e}")

    try:
        await dispose_db()
    except Exception as e:
        logger.error(f"Error disposing database resources: {e}")

    logger.info("Shutdown sequence completed. Exiting.")
    sys.exit(0)

if __name__ == "__main__":
    # Suppress RuntimeWarnings for unawaited coroutines and AttributeError during shutdown
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    try:
        import asyncio
        asyncio.run(main())
    except AttributeError as e:
        # Suppress attribute errors that may occur if references are cleaned up during shutdown
        import sys
        print(f"[SHUTDOWN] AttributeError suppressed during shutdown: {e}", file=sys.stderr)
    except Exception as e:
        import sys
        print(f"[SHUTDOWN] Exception during shutdown: {e}", file=sys.stderr)