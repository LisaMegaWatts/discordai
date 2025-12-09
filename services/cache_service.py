"""
Response caching service for Discord bot.

Provides in-memory caching for common queries and responses to improve
bot responsiveness and reduce API calls.
"""

import hashlib
import time
from typing import Optional, Dict, Tuple
import asyncio


class ResponseCache:
    """
    In-memory cache for bot responses with TTL and LRU eviction.
    
    Attributes:
        cache: Dictionary storing cached responses with metadata
        ttl: Time-to-live in seconds for cached entries
        max_size: Maximum number of entries before LRU eviction
        lock: Async lock for thread-safe operations
    """
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        """
        Initialize the response cache.
        
        Args:
            ttl_seconds: Time-to-live for cached entries (default: 5 minutes)
            max_size: Maximum cache size before LRU eviction (default: 1000)
        """
        self.cache: Dict[str, Tuple[str, float, int]] = {}  # key -> (response, timestamp, access_count)
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.lock = asyncio.Lock()
        
        # Metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def _generate_key(self, user_message: str, intent: str = None) -> str:
        """
        Generate cache key from message and optional intent.
        
        Args:
            user_message: User's message text
            intent: Optional intent classification
            
        Returns:
            Hash-based cache key
        """
        # Normalize message: lowercase, strip whitespace
        normalized = user_message.lower().strip()
        
        # Include intent in key if provided
        if intent:
            key_base = f"{intent}:{normalized}"
        else:
            key_base = normalized
        
        # Generate hash for consistent key length
        return hashlib.md5(key_base.encode()).hexdigest()
    
    async def get(self, user_message: str, intent: str = None) -> Optional[str]:
        """
        Get cached response if exists and not expired.
        
        Args:
            user_message: User's message text
            intent: Optional intent classification
            
        Returns:
            Cached response if found and valid, None otherwise
        """
        async with self.lock:
            key = self._generate_key(user_message, intent)
            
            if key not in self.cache:
                self.misses += 1
                return None
            
            response, timestamp, access_count = self.cache[key]
            current_time = time.time()
            
            # Check if expired
            if current_time - timestamp > self.ttl:
                del self.cache[key]
                self.misses += 1
                return None
            
            # Update access count for LRU
            self.cache[key] = (response, timestamp, access_count + 1)
            self.hits += 1
            return response
    
    async def set(self, user_message: str, response: str, intent: str = None):
        """
        Store response in cache with timestamp.
        
        Args:
            user_message: User's message text
            response: Bot's response to cache
            intent: Optional intent classification
        """
        async with self.lock:
            # Check if cache is full
            if len(self.cache) >= self.max_size:
                await self._evict_lru()
            
            key = self._generate_key(user_message, intent)
            current_time = time.time()
            
            # Store with timestamp and initial access count
            self.cache[key] = (response, current_time, 1)
    
    async def _evict_lru(self):
        """
        Evict least recently used entry when cache is full.
        Uses access count and timestamp to determine LRU.
        """
        if not self.cache:
            return
        
        # Find entry with lowest access count and oldest timestamp
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k][2], self.cache[k][1])  # (access_count, timestamp)
        )
        
        del self.cache[lru_key]
        self.evictions += 1
    
    async def clear_expired(self):
        """
        Remove all expired entries from cache.
        Should be called periodically to free memory.
        """
        async with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp, _) in self.cache.items()
                if current_time - timestamp > self.ttl
            ]
            
            for key in expired_keys:
                del self.cache[key]
    
    async def clear_user_cache(self, user_id: str):
        """
        Clear cache entries for a specific user.
        
        Note: Current implementation uses content-based keys,
        not user-specific keys. This method is a placeholder
        for future user-specific caching.
        
        Args:
            user_id: Discord user ID
        """
        # Placeholder for user-specific cache clearing
        # Current implementation uses content-based keys only
        pass
    
    async def clear_all(self):
        """Clear all cached entries."""
        async with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(hit_rate, 2),
            "max_size": self.max_size
        }
    
    def is_cacheable_intent(self, intent: str) -> bool:
        """
        Determine if an intent's response should be cached.
        
        Args:
            intent: Intent classification
            
        Returns:
            True if intent responses should be cached
        """
        # Don't cache personalized or action intents
        non_cacheable = {
            "generate_image",
            "submit_feature",
            "action_query",
            "unknown"
        }
        
        return intent not in non_cacheable