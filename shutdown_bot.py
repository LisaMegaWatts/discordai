# shutdown_bot.py

import asyncio
import logging
import sys

from discord_bot import bot  # Assumes bot is imported from discord_bot.py
from db import engine, AsyncSessionLocal  # Correct import from db.py

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
    await bot.close()
    logger.info("Discord bot stopped.")

async def cancel_background_tasks():
    logger.info("Cancelling all background tasks...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("All background tasks cancelled.")

async def dispose_db():
    logger.info("Disposing SQLAlchemy engine and closing AsyncSession objects...")

    # Await and close AsyncSession objects
    try:
        # Close AsyncSessionLocal if needed (sessionmaker does not need closing, but included for symmetry)
        if AsyncSessionLocal:
            logger.info("AsyncSessionLocal is a factory, no session to close directly.")
    except Exception as e:
        logger.error(f"Error closing AsyncSession: {e}")

    # Dispose and dereference engine
    try:
        if engine:
            await engine.dispose()
            logger.info("AsyncEngine disposed and dereferenced.")
            del engine
    except Exception as e:
        logger.error(f"Error disposing engine: {e}")

    # Final cleanup: Remove lingering AsyncEngine references
    import gc
    gc.collect()
    logger.info("Garbage collection complete. Checking for lingering AsyncEngine/AsyncSession objects...")

    # Confirm no lingering AsyncEngine/AsyncSession objects
    import inspect
    found_engines = []
    found_sessions = []
    for obj in gc.get_objects():
        try:
            if obj.__class__.__name__ == "AsyncEngine":
                found_engines.append(obj)
            if obj.__class__.__name__ == "AsyncSession":
                found_sessions.append(obj)
        except Exception:
            continue
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
    # Suppress RuntimeWarnings for unawaited coroutines by ensuring all are awaited
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    asyncio.run(main())