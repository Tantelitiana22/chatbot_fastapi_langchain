"""
Cache Service Implementation - Response caching
"""
from typing import Dict, Optional

from chat_app.application.use_cases import CacheService
from chat_app.domain.value_objects import CacheKey


class InMemoryCacheService(CacheService):
    """In-memory implementation of cache service"""

    def __init__(self, cache_size_limit: int = 100):
        self.cache: Dict[str, str] = {}
        self.cache_size_limit = cache_size_limit

    async def get_cached_response(self, cache_key: CacheKey) -> Optional[str]:
        """Get cached response if available"""
        return self.cache.get(cache_key.value)

    async def cache_response(self, cache_key: CacheKey, response: str) -> None:
        """Cache response for future use"""
        # Limit cache size
        if len(self.cache) >= self.cache_size_limit:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[cache_key.value] = response

    async def clear_cache(self) -> None:
        """Clear all cached responses"""
        self.cache.clear()
        print("Response cache cleared")
