import os
import logging

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.enabled = redis is not None
        self.client = None
        if self.enabled:
            self.client = redis.from_url(self.url, decode_responses=True)

    async def set_if_not_exists(self, key, value, expire_seconds=3600):
        if not self.enabled:
            # Fallback: always return True (simulate atomic set)
            return True
        try:
            result = await self.client.set(key, value, ex=expire_seconds, nx=True)
            return result is True
        except Exception as e:
            logger.error(f"Redis set_if_not_exists error: {e}")
            return True

    async def exists(self, key):
        if not self.enabled:
            return False
        try:
            return await self.client.exists(key)
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def set(self, key, value, expire_seconds=3600):
        if not self.enabled:
            return True
        try:
            await self.client.set(key, value, ex=expire_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return True

    async def get(self, key):
        if not self.enabled:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def delete(self, key):
        if not self.enabled:
            return True
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return True