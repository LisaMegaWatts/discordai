import os
import logging
import asyncio
 
try:
    import redis.asyncio as redis
except ImportError:
    redis = None
 
logger = logging.getLogger(__name__)
REDIS_MAX_RETRIES = 3
REDIS_RETRY_DELAY = 1  # seconds
REDIS_ALERT_THRESHOLD = 5  # consecutive failures before alerting

class RedisAlertState:
    consecutive_failures = 0

class RedisClient:
    def __init__(self):
        self.url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = redis is not None
        self.client = None
        self._connection_tested = False
        logger.debug(f"[RedisClient.__init__] enabled={self.enabled}, url={self.url}")

    async def initialize(self):
        """Async initialization for Redis connection and ping test."""
        logger.debug("[RedisClient.initialize] Called")
        if self.enabled and self.client is None:
            try:
                self.client = redis.from_url(self.url, decode_responses=True)
                await self.client.ping()
                self._connection_tested = True
                logger.info("[RedisClient.initialize] Redis client initialized and ping successful")
            except Exception as e:
                logger.error(f"Redis connection failed during async init: {e}")
                self.enabled = False
                self.client = None
                self._connection_tested = False

    async def _retry(self, coro, *args, fallback=None, **kwargs):
        import asyncio
        def is_event_loop_closed():
            try:
                loop = asyncio.get_running_loop()
                return loop.is_closed()
            except RuntimeError:
                return True
        for attempt in range(1, REDIS_MAX_RETRIES + 1):
            if is_event_loop_closed():
                logger.error("[DIAG] Attempted Redis operation after event loop closed.")
            try:
                if self.client is None:
                    raise ConnectionError("Redis client is None")
                # Ensure connection is tested before any operation
                if hasattr(self, "initialize") and not getattr(self, "_connection_tested", False):
                    await self.initialize()
                    if not self.enabled or self.client is None:
                        raise ConnectionError("Redis client failed async initialization")
                return await coro(*args, **kwargs)
            except Exception as e:
                RedisAlertState.consecutive_failures += 1
                logger.error(f"Redis error (attempt {attempt}): {e}")
                if RedisAlertState.consecutive_failures >= REDIS_ALERT_THRESHOLD:
                    logger.critical("Persistent Redis failure detected. Alerting system administrator.")
                await asyncio.sleep(REDIS_RETRY_DELAY)
        # Fallback logic
        if fallback is not None:
            logger.warning("Falling back to DB logic due to Redis failure.")
            # Support async fallback
            if asyncio.iscoroutinefunction(fallback):
                try:
                    return await fallback()
                except Exception as fallback_e:
                    logger.error(f"Fallback coroutine failed: {fallback_e}")
                    return None
            else:
                try:
                    return fallback()
                except Exception as fallback_e:
                    logger.error(f"Fallback function failed: {fallback_e}")
                    return None
        return None

    async def set_if_not_exists(self, key, value, expire_seconds=3600):
        if not self.enabled:
            # Fallback: always return True (simulate atomic set)
            return True
        if self.client is None:
            logger.error(f"[RedisClient.set_if_not_exists] self.client is None for key={key}")
        def fallback():
            # Fallback: always return True (simulate atomic set)
            return True
        result = await self._retry(
            self.client.set, key, value, ex=expire_seconds, nx=True, fallback=fallback
        )
        # Reset alert state on success
        if result is True:
            RedisAlertState.consecutive_failures = 0
        return result is True

    async def exists(self, key):
        if not self.enabled:
            return False
        def fallback():
            return False
        result = await self._retry(
            self.client.exists, key, fallback=fallback
        )
        if result:
            RedisAlertState.consecutive_failures = 0
        return bool(result)

    async def set(self, key, value, expire_seconds=3600):
        if not self.enabled:
            return True
        def fallback():
            return True
        result = await self._retry(
            self.client.set, key, value, ex=expire_seconds, fallback=fallback
        )
        if result is not None:
            RedisAlertState.consecutive_failures = 0
        return True

    async def get(self, key):
        if not self.enabled:
            return None
        def fallback():
            return None
        result = await self._retry(
            self.client.get, key, fallback=fallback
        )
        if result is not None:
            RedisAlertState.consecutive_failures = 0
        return result

    async def delete(self, key):
        if not self.enabled:
            return True
        def fallback():
            return True
        result = await self._retry(
            self.client.delete, key, fallback=fallback
        )
        if result is not None:
            RedisAlertState.consecutive_failures = 0
        return True