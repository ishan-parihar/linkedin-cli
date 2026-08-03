"""
Async/await patterns for concurrent Obscura operations.

Provides async utilities for efficient concurrent execution of Obscura
operations to improve performance for parallel requests.
"""

import asyncio
import logging
from typing import Any, Callable, Awaitable, List, Dict
import time

from linkedin_mcp_server.core.feature_flags import is_obscura_advanced_feature_enabled

logger = logging.getLogger(__name__)


class AsyncObscuraExecutor:
    """Execute Obscura operations concurrently with proper async handling."""

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: float = 30.0,
    ):
        self.max_concurrent = max_concurrent
        self.timeout = timeout

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks: set = set()
        self._task_stats: dict = {}

        logger.info(
            "Async Obscura executor initialized: max_concurrent=%d, timeout=%s",
            max_concurrent,
            timeout,
        )

    async def execute(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        """Execute a single Obscura operation with concurrency control."""
        async with self._semaphore:
            task_id = id(asyncio.current_task())
            start_time = time.time()

            try:
                logger.debug("Executing task %s", task_id)
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)

                duration = time.time() - start_time
                self._record_task_stats(task_id, duration, True)

                return result

            except asyncio.TimeoutError:
                duration = time.time() - start_time
                self._record_task_stats(task_id, duration, False)
                logger.error("Task %s timed out after %.3fs", task_id, duration)
                raise TimeoutError(f"Obscura operation timed out after {self.timeout}s")

            except Exception as e:
                duration = time.time() - start_time
                self._record_task_stats(task_id, duration, False)
                logger.error("Task %s failed after %.3fs: %s", task_id, duration, e)
                raise

    async def execute_concurrent(
        self, operations: List[tuple[Callable[..., Awaitable[Any]], tuple, dict]]
    ) -> List[Any]:
        """Execute multiple Obscura operations concurrently.

        Args:
            operations: List of (function, args, kwargs) tuples

        Returns:
            List of results in the same order as operations
        """
        if not is_obscura_advanced_feature_enabled("caching"):
            # Execute sequentially if caching disabled
            results = []
            for func, args, kwargs in operations:
                result = await func(*args, **kwargs)
                results.append(result)
            return results

        logger.info("Executing %d operations concurrently", len(operations))
        start_time = time.time()

        # Create tasks for all operations
        tasks = [self.execute(func, *args, **kwargs) for func, args, kwargs in operations]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error("Operation %d failed: %s", i, result)

            duration = time.time() - start_time
            logger.info(
                "Completed %d concurrent operations in %.3fs (%.3fs per operation)",
                len(operations),
                duration,
                duration / len(operations),
            )

            return results

        except Exception as e:
            logger.error("Concurrent execution failed: %s", e)
            raise

    async def execute_parallel_map(
        self, func: Callable[..., Awaitable[Any]], items: List[Any], **fixed_kwargs: Any
    ) -> List[Any]:
        """Execute a function concurrently over a list of items.

        Args:
            func: Async function to execute
            items: List of items to process
            fixed_kwargs: Fixed kwargs to pass to each function call

        Returns:
            List of results in the same order as items
        """
        operations = [(func, (item,), fixed_kwargs) for item in items]
        return await self.execute_concurrent(operations)

    def _record_task_stats(self, task_id: int, duration: float, success: bool) -> None:
        """Record statistics for a completed task."""
        self._task_stats[task_id] = {
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
        }

        # Keep only recent stats
        if len(self._task_stats) > 1000:
            # Remove oldest entries
            sorted_by_time = sorted(self._task_stats.items(), key=lambda x: x[1]["timestamp"])
            for task_id_to_remove, _ in sorted_by_time[:500]:
                del self._task_stats[task_id_to_remove]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for executed tasks."""
        if not self._task_stats:
            return {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "avg_duration": 0,
                "success_rate": 0,
            }

        successful = [s for s in self._task_stats.values() if s["success"]]
        durations = [s["duration"] for s in self._task_stats.values()]

        return {
            "total_tasks": len(self._task_stats),
            "successful_tasks": len(successful),
            "failed_tasks": len(self._task_stats) - len(successful),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "success_rate": len(successful) / len(self._task_stats) if self._task_stats else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
        }


class ObscuraAsyncAdapter:
    """Adapter to make Obscura operations more async-friendly."""

    def __init__(self, obscura_browser):
        self.obscura_browser = obscura_browser
        self.executor = AsyncObscuraExecutor()

    async def fetch_multiple_pages(self, urls: List[str]) -> Dict[str, str]:
        """Fetch multiple pages concurrently.

        Args:
            urls: List of URLs to fetch

        Returns:
            Dictionary mapping URLs to their HTML content
        """

        async def fetch_single(url: str) -> tuple[str, str]:
            await self.obscura_browser.goto(url)
            content = await self.obscura_browser.content()
            return url, content

        operations = [(fetch_single, (url,), {}) for url in urls]
        results = await self.executor.execute_concurrent(operations)

        # Convert results to dictionary
        url_to_content = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error("Failed to fetch page: %s", result)
            else:
                url, content = result
                url_to_content[url] = content

        return url_to_content

    async def fetch_with_retry(
        self,
        url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> str:
        """Fetch a page with retry logic.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Page content
        """
        for attempt in range(max_retries):
            try:
                await self.obscura_browser.goto(url)
                return await self.obscura_browser.content()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(
                    "Fetch attempt %d failed for %s: %s. Retrying in %.1fs...",
                    attempt + 1,
                    url,
                    e,
                    retry_delay,
                )
                await asyncio.sleep(retry_delay)

    async def fetch_with_timeout(
        self,
        url: str,
        timeout: float = 30.0,
    ) -> str:
        """Fetch a page with a specific timeout.

        Args:
            url: URL to fetch
            timeout: Timeout in seconds

        Returns:
            Page content
        """
        try:
            return await asyncio.wait_for(self._fetch_with_retry(url), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Fetch timeout for {url} after {timeout}s")

    async def _fetch_with_retry(self, url: str) -> str:
        """Internal fetch method that uses retry logic."""
        return await self.fetch_with_retry(url)


# Global async executor instance
_async_executor: AsyncObscuraExecutor | None = None


def get_async_executor() -> AsyncObscuraExecutor:
    """Get the global async executor instance."""
    global _async_executor

    if _async_executor is None:
        _async_executor = AsyncObscuraExecutor()

    return _async_executor


async def initialize_async_executor(max_concurrent: int = 10) -> None:
    """Initialize the async executor with specific settings."""
    global _async_executor

    _async_executor = AsyncObscuraExecutor(max_concurrent=max_concurrent)
    logger.info("Initialized async executor with max_concurrent=%d", max_concurrent)
