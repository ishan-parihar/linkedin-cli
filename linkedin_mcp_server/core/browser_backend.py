"""
Browser backend configuration - Obscura-only implementation.

This module provides configuration for the Obscura browser backend.
Playwright support has been completely removed in favor of Obscura.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BackendConfig:
    """Configuration for browser backend."""

    def __init__(
        self,
        backend: str = "obscura",
        use_obscura: bool = True,
        force_obscura: bool = True,
        playwright_fallback: bool = False,
    ):
        self.backend = backend
        self.use_obscura = use_obscura
        self.force_obscura = force_obscura
        self.playwright_fallback = playwright_fallback


def get_backend_config() -> BackendConfig:
    """Get the current backend configuration.

    Always returns Obscura configuration as Playwright has been removed.
    """
    return BackendConfig(
        backend="obscura",
        use_obscura=True,
        force_obscura=True,
        playwright_fallback=False,
    )


def should_use_obscura() -> bool:
    """Check if Obscura should be used (always True)."""
    return True


def should_fallback_to_playwright() -> bool:
    """Check if Playwright fallback is enabled (always False)."""
    return False


def get_browser_backend() -> str:
    """Get the current browser backend (always 'obscura')."""
    return "obscura"


def is_obscura_enabled() -> bool:
    """Check if Obscura is enabled (always True)."""
    return True


def is_playwright_enabled() -> bool:
    """Check if Playwright is enabled (always False)."""
    return False
