"""Authentication functions for LinkedIn (Obscura-compatible)."""

import asyncio
import logging
import re
from urllib.parse import urlparse
from typing import Any

from .exceptions import AuthenticationError

logger = logging.getLogger(__name__)

_AUTH_BLOCKER_URL_PATTERNS = (
    "/login",
    "/authwall",
    "/checkpoint",
    "/challenge",
    "/uas/login",
    "/uas/consumer-email-challenge",
)


async def is_logged_in(page: Any) -> bool:
    """Check if the user is logged in to LinkedIn."""
    try:
        url = page.url if hasattr(page, "url") else page.current_url
        if url:
            for pattern in _AUTH_BLOCKER_URL_PATTERNS:
                if pattern in url:
                    return False
        return True
    except Exception as e:
        logger.warning("Error checking login status: %s", e)
        return False


async def detect_auth_barrier(page: Any) -> str | None:
    """Detect authentication barriers on LinkedIn."""
    try:
        url = page.url if hasattr(page, "url") else page.current_url
        for pattern in _AUTH_BLOCKER_URL_PATTERNS:
            if pattern in url:
                return pattern
        return None
    except Exception as e:
        logger.warning("Error detecting auth barrier: %s", e)
        return None


async def detect_auth_barrier_quick(page: Any) -> str | None:
    """Quick detection of authentication barriers."""
    return await detect_auth_barrier(page)


async def resolve_remember_me_prompt(page: Any) -> bool:
    """Resolve remember-me prompt (simplified for Obscura)."""
    # Obscura doesn't support interactive elements
    # This is a no-op for Obscura backend
    return False


async def wait_for_manual_login(page: Any, timeout: int = 300000) -> None:
    """Wait for manual login (simplified for Obscura)."""
    # Obscura doesn't support interactive login
    # This is a no-op for Obscura backend
    pass
