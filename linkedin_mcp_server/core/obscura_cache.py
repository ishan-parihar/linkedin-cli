"""
Caching strategies for repeated Obscura requests.

Provides intelligent caching to improve performance for repeated requests
to the same LinkedIn pages or similar content.
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional
import tempfile

from linkedin_mcp_server.core.feature_flags import is_obscura_advanced_feature_enabled

logger = logging.getLogger(__name__)


class ObscuraCache:
    """Cache for Obscura fetch results to improve performance."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_size: int = 1000,
        ttl: float = 300.0,  # 5 minutes default TTL
    ):
        self.cache_dir = cache_dir or Path(tempfile.mkdtemp(prefix="obscura_cache_"))
        self.max_size = max_size
        self.ttl = ttl

        self._memory_cache: dict = {}
        self._cache_stats: dict = {"hits": 0, "misses": 0, "evictions": 0}

        self._cache_lock = asyncio.Lock()

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Obscura cache initialized: cache_dir=%s, max_size=%d, ttl=%s",
            self.cache_dir,
            max_size,
            ttl,
        )

    def _generate_cache_key(self, url: str, method: str = "fetch") -> str:
        """Generate a cache key for a request."""
        key_data = f"{method}:{url}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get(self, url: str, method: str = "fetch") -> Optional[str]:
        """Get cached content for a URL."""
        if not is_obscura_advanced_feature_enabled("caching"):
            return None

        cache_key = self._generate_cache_key(url, method)

        async with self._cache_lock:
            # Check memory cache first
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if self._is_entry_valid(entry):
                    self._cache_stats["hits"] += 1
                    logger.debug("Cache hit (memory): %s", cache_key)
                    return entry["content"]
                else:
                    # Remove expired entry
                    del self._memory_cache[cache_key]
                    self._cache_stats["evictions"] += 1

            # Check disk cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    entry_data = json.loads(cache_file.read_text())
                    if self._is_entry_valid(entry_data):
                        # Add to memory cache
                        self._memory_cache[cache_key] = entry_data
                        self._cache_stats["hits"] += 1
                        logger.debug("Cache hit (disk): %s", cache_key)
                        return entry_data["content"]
                    else:
                        # Remove expired file
                        cache_file.unlink()
                        self._cache_stats["evictions"] += 1
                except Exception as e:
                    logger.warning("Failed to read cache file %s: %s", cache_file, e)

            self._cache_stats["misses"] += 1
            logger.debug("Cache miss: %s", cache_key)
            return None

    async def set(self, url: str, content: str, method: str = "fetch") -> None:
        """Cache content for a URL."""
        if not is_obscura_advanced_feature_enabled("caching"):
            return

        cache_key = self._generate_cache_key(url, method)

        entry = {
            "url": url,
            "method": method,
            "content": content,
            "created_at": time.time(),
            "size": len(content),
        }

        async with self._cache_lock:
            # Add to memory cache
            self._memory_cache[cache_key] = entry

            # Enforce max size
            if len(self._memory_cache) > self.max_size:
                await self._evict_lru()

            # Write to disk cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            try:
                cache_file.write_text(json.dumps(entry))
                logger.debug("Cached content: %s (%d bytes)", cache_key, len(content))
            except Exception as e:
                logger.warning("Failed to write cache file %s: %s", cache_file, e)

    def _is_entry_valid(self, entry: dict) -> bool:
        """Check if a cache entry is still valid."""
        age = time.time() - entry["created_at"]
        return age < self.ttl

    async def _evict_lru(self) -> None:
        """Evict least recently used entries from memory cache."""
        if not self._memory_cache:
            return

        # Sort by creation time and remove oldest entries
        sorted_entries = sorted(self._memory_cache.items(), key=lambda x: x[1]["created_at"])

        # Remove 10% of entries
        entries_to_remove = max(1, len(sorted_entries) // 10)
        for cache_key, _ in sorted_entries[:entries_to_remove]:
            del self._memory_cache[cache_key]
            self._cache_stats["evictions"] += 1

        logger.debug("Evicted %d LRU cache entries", entries_to_remove)

    async def invalidate(self, url: str, method: str = "fetch") -> None:
        """Invalidate cache entry for a URL."""
        cache_key = self._generate_cache_key(url, method)

        async with self._cache_lock:
            # Remove from memory cache
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]

            # Remove from disk cache
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_file.unlink()

            logger.debug("Invalidated cache entry: %s", cache_key)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._cache_lock:
            self._memory_cache.clear()

            # Clear disk cache
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning("Failed to delete cache file %s: %s", cache_file, e)

            logger.info("Cleared all cache entries")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        async with self._cache_lock:
            hit_rate = 0
            total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
            if total_requests > 0:
                hit_rate = self._cache_stats["hits"] / total_requests

            return {
                "memory_cache_size": len(self._memory_cache),
                "disk_cache_files": len(list(self.cache_dir.glob("*.json"))),
                "hits": self._cache_stats["hits"],
                "misses": self._cache_stats["misses"],
                "evictions": self._cache_stats["evictions"],
                "hit_rate": hit_rate,
                "max_size": self.max_size,
                "ttl": self.ttl,
            }


class CacheKeyGenerator:
    """Generate cache keys for different types of LinkedIn content."""

    @staticmethod
    def profile_key(username: str) -> str:
        """Generate cache key for LinkedIn profile."""
        return f"profile:{username}"

    @staticmethod
    def company_key(company_id: str) -> str:
        """Generate cache key for LinkedIn company."""
        return f"company:{company_id}"

    @staticmethod
    def feed_key(params: dict) -> str:
        """Generate cache key for LinkedIn feed."""
        params_str = json.dumps(params, sort_keys=True)
        return f"feed:{hashlib.md5(params_str.encode()).hexdigest()}"

    @staticmethod
    def search_key(query: str, filters: dict) -> str:
        """Generate cache key for LinkedIn search."""
        filters_str = json.dumps(filters, sort_keys=True)
        combined = f"{query}:{filters_str}"
        return f"search:{hashlib.md5(combined.encode()).hexdigest()}"


# Global cache instance
_obscura_cache: ObscuraCache | None = None


def get_obscura_cache() -> ObscuraCache:
    """Get the global Obscura cache instance."""
    global _obscura_cache

    if not is_obscura_advanced_feature_enabled("caching"):
        return ObscuraCache(max_size=0)  # Disabled

    if _obscura_cache is None:
        _obscura_cache = ObscuraCache()

    return _obscura_cache


async def initialize_cache(cache_dir: Optional[Path] = None, max_size: int = 1000) -> None:
    """Initialize the cache with specific settings."""
    global _obscura_cache

    if _obscura_cache is not None:
        await _obscura_cache.clear()

    _obscura_cache = ObscuraCache(cache_dir=cache_dir, max_size=max_size)
    logger.info("Initialized cache with max_size=%d", max_size)


async def close_cache() -> None:
    """Close the cache and cleanup resources."""
    global _obscura_cache

    if _obscura_cache is not None:
        await _obscura_cache.clear()
        _obscura_cache = None
        logger.info("Cache closed")
