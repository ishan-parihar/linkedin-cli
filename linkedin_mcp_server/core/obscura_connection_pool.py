"""
Connection pooling for Obscura browser instances.

Provides connection pooling to improve sequential operation performance
by reusing Obscura processes and storage directories across requests.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any
from collections import deque
import time

from linkedin_mcp_server.core.feature_flags import is_obscura_advanced_feature_enabled

logger = logging.getLogger(__name__)


class ObscuraConnectionPool:
    """Connection pool for Obscura browser instances.
    
    Reuses Obscura processes and storage directories to improve
    sequential operation performance by reducing startup overhead.
    """
    
    def __init__(
        self,
        max_connections: int = 5,
        max_idle_time: float = 30.0,
        max_lifetime: float = 300.0,
    ):
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.max_lifetime = max_lifetime
        
        self._available_connections: deque = deque()
        self._active_connections: set = set()
        self._connection_metadata: dict = {}
        
        self._pool_lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None
        self._running = False
        
        logger.info(
            "Obscura connection pool initialized: max_connections=%d, max_idle_time=%s, max_lifetime=%s",
            max_connections, max_idle_time, max_lifetime
        )
    
    async def acquire(self) -> str:
        """Acquire a connection from the pool.
        
        Returns a connection ID that can be used to retrieve the connection.
        """
        async with self._pool_lock:
            # Try to get an available connection
            while self._available_connections:
                conn_id = self._available_connections.popleft()
                metadata = self._connection_metadata.get(conn_id)
                
                # Check if connection is still valid
                if metadata and self._is_connection_valid(metadata):
                    self._active_connections.add(conn_id)
                    metadata["last_used"] = time.time()
                    logger.debug("Acquired existing connection: %s", conn_id)
                    return conn_id
                else:
                    # Remove invalid connection
                    self._remove_connection(conn_id)
            
            # Create new connection if under limit
            if len(self._active_connections) < self.max_connections:
                conn_id = await self._create_connection()
                self._active_connections.add(conn_id)
                logger.debug("Created new connection: %s", conn_id)
                return conn_id
            
            # Wait for an available connection
            logger.warning("Connection pool exhausted, waiting for available connection")
            raise Exception("Connection pool exhausted")
    
    async def release(self, conn_id: str) -> None:
        """Release a connection back to the pool."""
        async with self._pool_lock:
            if conn_id in self._active_connections:
                self._active_connections.remove(conn_id)
                metadata = self._connection_metadata.get(conn_id)
                
                if metadata and self._is_connection_valid(metadata):
                    self._available_connections.append(conn_id)
                    metadata["last_used"] = time.time()
                    logger.debug("Released connection: %s", conn_id)
                else:
                    self._remove_connection(conn_id)
    
    async def _create_connection(self) -> str:
        """Create a new Obscura connection."""
        import uuid
        conn_id = str(uuid.uuid4())
        
        # Create temporary storage directory for this connection
        storage_dir = Path(tempfile.mkdtemp(prefix="obscura_pool_"))
        
        metadata = {
            "created_at": time.time(),
            "last_used": time.time(),
            "storage_dir": str(storage_dir),
            "request_count": 0,
        }
        
        self._connection_metadata[conn_id] = metadata
        logger.info("Created new Obscura connection: %s with storage: %s", conn_id, storage_dir)
        
        return conn_id
    
    def _is_connection_valid(self, metadata: dict) -> bool:
        """Check if a connection is still valid."""
        now = time.time()
        
        # Check idle time
        if now - metadata["last_used"] > self.max_idle_time:
            logger.debug("Connection expired due to idle time")
            return False
        
        # Check lifetime
        if now - metadata["created_at"] > self.max_lifetime:
            logger.debug("Connection expired due to lifetime")
            return False
        
        # Check if storage directory still exists
        storage_dir = Path(metadata["storage_dir"])
        if not storage_dir.exists():
            logger.debug("Connection storage directory missing")
            return False
        
        return True
    
    def _remove_connection(self, conn_id: str) -> None:
        """Remove a connection from the pool."""
        if conn_id in self._active_connections:
            self._active_connections.remove(conn_id)
        
        # Remove from available if present
        try:
            self._available_connections.remove(conn_id)
        except ValueError:
            pass
        
        # Clean up metadata and storage
        metadata = self._connection_metadata.pop(conn_id, None)
        if metadata:
            storage_dir = Path(metadata["storage_dir"])
            try:
                import shutil
                shutil.rmtree(storage_dir, ignore_errors=True)
                logger.debug("Cleaned up connection storage: %s", storage_dir)
            except Exception as e:
                logger.warning("Failed to clean up storage %s: %s", storage_dir, e)
    
    async def start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Started connection pool cleanup task")
    
    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        logger.info("Stopped connection pool cleanup task")
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while self._running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self._cleanup_expired_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cleanup loop error: %s", e)
    
    async def _cleanup_expired_connections(self) -> None:
        """Clean up expired connections."""
        async with self._pool_lock:
            expired_connections = []
            
            # Check available connections
            for conn_id in list(self._available_connections):
                metadata = self._connection_metadata.get(conn_id)
                if metadata and not self._is_connection_valid(metadata):
                    expired_connections.append(conn_id)
            
            # Remove expired connections
            for conn_id in expired_connections:
                self._remove_connection(conn_id)
                logger.info("Cleaned up expired connection: %s", conn_id)
    
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        await self.stop_cleanup_task()
        
        async with self._pool_lock:
            # Remove all connections
            all_conn_ids = list(self._available_connections) + list(self._active_connections)
            for conn_id in all_conn_ids:
                self._remove_connection(conn_id)
            
            logger.info("Closed all connections in pool")
    
    def get_pool_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        return {
            "total_connections": len(self._connection_metadata),
            "active_connections": len(self._active_connections),
            "available_connections": len(self._available_connections),
            "max_connections": self.max_connections,
            "running": self._running,
        }
    
    def get_connection_metadata(self, conn_id: str) -> dict[str, Any] | None:
        """Get metadata for a specific connection."""
        return self._connection_metadata.get(conn_id)


# Global connection pool instance
_connection_pool: ObscuraConnectionPool | None = None


def get_connection_pool() -> ObscuraConnectionPool:
    """Get the global connection pool instance."""
    global _connection_pool
    
    if not is_obscura_advanced_feature_enabled("connection_pooling"):
        logger.info("Connection pooling disabled via feature flags")
        # Return a disabled/no-op pool
        return ObscuraConnectionPool(max_connections=0)
    
    if _connection_pool is None:
        _connection_pool = ObscuraConnectionPool()
        # Start cleanup task in background
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_connection_pool.start_cleanup_task())
        except RuntimeError:
            logger.warning("No event loop running, cleanup task not started")
    
    return _connection_pool


async def initialize_connection_pool(max_connections: int = 5) -> None:
    """Initialize the connection pool with specific settings."""
    global _connection_pool
    
    if _connection_pool is not None:
        await _connection_pool.close_all()
    
    _connection_pool = ObscuraConnectionPool(max_connections=max_connections)
    await _connection_pool.start_cleanup_task()
    logger.info("Initialized connection pool with max_connections=%d", max_connections)


async def close_connection_pool() -> None:
    """Close the connection pool and cleanup resources."""
    global _connection_pool
    
    if _connection_pool is not None:
        await _connection_pool.close_all()
        _connection_pool = None
        logger.info("Connection pool closed")