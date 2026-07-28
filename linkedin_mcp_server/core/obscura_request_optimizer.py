"""
Request batching and optimization for Obscura operations.

Provides request batching to improve sequential operation performance
by grouping multiple requests and optimizing their execution.
"""

import asyncio
import logging
from typing import Any, Callable, Awaitable
from collections import defaultdict
import time

from linkedin_mcp_server.core.feature_flags import is_obscura_advanced_feature_enabled

logger = logging.getLogger(__name__)


class RequestBatcher:
    """Batch multiple Obscura requests for improved performance."""
    
    def __init__(
        self,
        batch_size: int = 5,
        batch_timeout: float = 2.0,
        max_queue_size: int = 100,
    ):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_queue_size = max_queue_size
        
        self._request_queue: list = []
        self._pending_batches: dict = {}
        self._batch_counter = 0
        
        self._queue_lock = asyncio.Lock()
        self._processing = False
        
        logger.info(
            "Request batcher initialized: batch_size=%d, batch_timeout=%s, max_queue_size=%d",
            batch_size, batch_timeout, max_queue_size
        )
    
    async def add_request(
        self,
        request_func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Add a request to the batch queue and wait for completion."""
        if not is_obscura_advanced_feature_enabled("caching"):
            # If batching is disabled, execute directly
            return await request_func(*args, **kwargs)
        
        request_id = self._generate_request_id()
        future = asyncio.Future()
        
        async with self._queue_lock:
            if len(self._request_queue) >= self.max_queue_size:
                logger.warning("Request queue full, executing immediately")
                result = await request_func(*args, **kwargs)
                return result
            
            self._request_queue.append({
                "id": request_id,
                "func": request_func,
                "args": args,
                "kwargs": kwargs,
                "future": future,
                "added_at": time.time(),
            })
            
            logger.debug("Added request %s to batch queue (queue size: %d)", request_id, len(self._request_queue))
        
        # Trigger batch processing if needed
        if len(self._request_queue) >= self.batch_size:
            asyncio.create_task(self._process_batch())
        
        # Wait for result
        return await future
    
    async def _process_batch(self) -> None:
        """Process a batch of requests."""
        async with self._queue_lock:
            if self._processing or not self._request_queue:
                return
            
            self._processing = True
            batch = self._request_queue[:self.batch_size]
            self._request_queue = self._request_queue[self.batch_size:]
        
        batch_id = self._generate_batch_id()
        logger.info("Processing batch %s with %d requests", batch_id, len(batch))
        
        start_time = time.time()
        
        try:
            # Execute all requests in the batch
            results = await asyncio.gather(
                *[req["func"](*req["args"], **req["kwargs"]) for req in batch],
                return_exceptions=True
            )
            
            # Set results for each request
            for req, result in zip(batch, results):
                if isinstance(result, Exception):
                    req["future"].set_exception(result)
                else:
                    req["future"].set_result(result)
            
            duration = time.time() - start_time
            logger.info(
                "Batch %s completed: %d requests in %.3fs (%.3fs per request)",
                batch_id, len(batch), duration, duration / len(batch)
            )
            
        except Exception as e:
            logger.error("Batch %s failed: %s", batch_id, e)
            # Set exception for all requests in batch
            for req in batch:
                if not req["future"].done():
                    req["future"].set_exception(e)
        
        finally:
            async with self._queue_lock:
                self._processing = False
                
                # Process remaining requests if queue is still full
                if len(self._request_queue) >= self.batch_size:
                    asyncio.create_task(self._process_batch())
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return f"req_{time.time()}_{id(object())}"
    
    def _generate_batch_id(self) -> str:
        """Generate a unique batch ID."""
        self._batch_counter += 1
        return f"batch_{self._batch_counter}"
    
    async def flush(self) -> None:
        """Flush all pending requests by processing them immediately."""
        async with self._queue_lock:
            if not self._request_queue:
                return
            
            batch = self._request_queue.copy()
            self._request_queue.clear()
        
        logger.info("Flushing %d pending requests", len(batch))
        
        # Process each request individually (simpler for flush)
        for req in batch:
            try:
                result = await req["func"](*req["args"], **req["kwargs"])
                req["future"].set_result(result)
            except Exception as e:
                req["future"].set_exception(e)
    
    def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        return {
            "queue_size": len(self._request_queue),
            "processing": self._processing,
            "batch_size": self.batch_size,
            "max_queue_size": self.max_queue_size,
            "batches_processed": self._batch_counter,
        }


class RequestOptimizer:
    """Optimize Obscura requests through intelligent scheduling."""
    
    def __init__(self):
        self._request_patterns: dict = defaultdict(list)
        self._performance_stats: dict = {}
    
    def record_request(self, url: str, duration: float, success: bool) -> None:
        """Record request performance data."""
        pattern = self._extract_pattern(url)
        
        self._request_patterns[pattern].append({
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
        })
        
        # Keep only recent stats
        if len(self._request_patterns[pattern]) > 100:
            self._request_patterns[pattern] = self._request_patterns[pattern][-100:]
    
    def _extract_pattern(self, url: str) -> str:
        """Extract URL pattern for grouping similar requests."""
        # Simple pattern extraction based on URL structure
        if "/in/" in url:
            return "profile"
        elif "/company/" in url:
            return "company"
        elif "/feed/" in url:
            return "feed"
        elif "/jobs/" in url:
            return "jobs"
        else:
            return "other"
    
    def get_pattern_stats(self, pattern: str) -> dict[str, Any]:
        """Get performance statistics for a URL pattern."""
        requests = self._request_patterns.get(pattern, [])
        
        if not requests:
            return {"count": 0, "avg_duration": 0, "success_rate": 0}
        
        successful = [r for r in requests if r["success"]]
        durations = [r["duration"] for r in requests]
        
        return {
            "count": len(requests),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "success_rate": len(successful) / len(requests) if requests else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
        }
    
    def should_batch_request(self, url: str) -> bool:
        """Determine if a request should be batched based on patterns."""
        pattern = self._extract_pattern(url)
        stats = self.get_pattern_stats(pattern)
        
        # Batch if we have enough data and requests are consistently fast
        if stats["count"] > 10 and stats["avg_duration"] < 1.0:
            return True
        
        return False


# Global instances
_request_batcher: RequestBatcher | None = None
_request_optimizer: RequestOptimizer | None = None


def get_request_batcher() -> RequestBatcher:
    """Get the global request batcher instance."""
    global _request_batcher
    
    if not is_obscura_advanced_feature_enabled("caching"):
        return RequestBatcher(batch_size=0)  # Disabled
    
    if _request_batcher is None:
        _request_batcher = RequestBatcher()
    
    return _request_batcher


def get_request_optimizer() -> RequestOptimizer:
    """Get the global request optimizer instance."""
    global _request_optimizer
    
    if _request_optimizer is None:
        _request_optimizer = RequestOptimizer()
    
    return _request_optimizer


async def initialize_request_optimizer(batch_size: int = 5) -> None:
    """Initialize the request optimizer with specific settings."""
    global _request_batcher
    
    if _request_batcher is not None:
        await _request_batcher.flush()
    
    _request_batcher = RequestBatcher(batch_size=batch_size)
    logger.info("Initialized request optimizer with batch_size=%d", batch_size)