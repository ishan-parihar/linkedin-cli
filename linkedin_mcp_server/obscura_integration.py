"""
LinkedIn-specific ObscuraCookieManager integration.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from obscura_cookie_manager import (
    ObscuraCookieManager,
    FileCookieStorage,
    BrowserCookie3Extractor,
    CookieSource,
    CookieValidationResult,
    ReLoginRequiredError,
)
from linkedin_mcp_server.session_state import get_cookies_path
from linkedin_mcp_server.logging_config import logger

# Required cookies for LinkedIn
LINKEDIN_REQUIRED_COOKIES = ["li_at", "bscookie"]


class LinkedInCookieValidator:
    """Validates LinkedIn cookies by making an API call."""

    def __init__(self):
        self._extractor = None

    async def validate(self, cookies: dict[str, str]) -> bool:
        """Validate cookies by checking if we can access LinkedIn."""
        try:
            # Import here to avoid circular imports
            from linkedin_mcp_server.drivers.browser import get_or_create_browser
            from linkedin_mcp_server.scraping import LinkedInExtractor

            # Create a temporary browser with these cookies
            browser = await get_or_create_browser()
            page = browser.page

            # Set cookies
            cookie_list = [
                {"name": name, "value": value, "domain": ".linkedin.com", "path": "/"}
                for name, value in cookies.items()
            ]
            await page.context.add_cookies(cookie_list)

            # Try to access a page
            await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=10000)

            # Check if we're logged in
            is_logged_in = await page.evaluate("""() => {
                return !document.body.innerText.includes('Sign in') && 
                       !document.body.innerText.includes('Join now') &&
                       document.querySelector('[data-test-global-nav-me]') !== null;
            }""")

            return is_logged_in
        except Exception as e:
            logger.debug(f"LinkedIn cookie validation failed: {e}")
            return False


class LinkedInObscuraManager:
    """LinkedIn-specific wrapper around ObscuraCookieManager."""

    def __init__(self):
        self._manager: Optional[ObscuraCookieManager] = None
        self._validator = LinkedInCookieValidator()

    def _get_storage(self) -> FileCookieStorage:
        """Get file-based cookie storage."""
        return FileCookieStorage(get_cookies_path())

    def _get_extractor(self) -> BrowserCookie3Extractor:
        """Get browser cookie extractor (prefers Chrome/Arc)."""
        return BrowserCookie3Extractor("chrome")

    def _get_manager(self) -> ObscuraCookieManager:
        """Get or create the ObscuraCookieManager instance."""
        if self._manager is None:
            self._manager = ObscuraCookieManager(
                storage=self._get_storage(),
                extractor=self._get_extractor(),
                validator=self._validator.validate,
                required_cookies=LINKEDIN_REQUIRED_COOKIES,
                domain="linkedin.com",
                validation_interval=300,  # 5 minutes
                max_re_extraction_attempts=3,
                re_extraction_cooldown=60,
            )
        return self._manager

    async def get_valid_cookies(self, force_refresh: bool = False) -> CookieValidationResult:
        """Get valid cookies, performing validation and re-extraction as needed."""
        manager = self._get_manager()
        return await manager.get_cookies(force_refresh=force_refresh)

    async def force_re_extraction(self) -> CookieValidationResult:
        """Force re-extraction from browser (call after user logs in)."""
        manager = self._get_manager()
        return await manager.force_re_extraction()

    async def invalidate_and_trigger_relogin(self) -> None:
        """Invalidate auth and trigger re-login flow."""
        manager = self._get_manager()
        await manager.invalidate_and_trigger_relogin()

    def is_cache_valid(self) -> bool:
        """Check if cached cookies are within validation interval."""
        manager = self._get_manager()
        return manager.is_cache_valid()


# Global instance
_linkedin_obscura_manager: Optional[LinkedInObscuraManager] = None


def get_linkedin_obscura_manager() -> LinkedInObscuraManager:
    """Get the global LinkedIn Obscura manager instance."""
    global _linkedin_obscura_manager
    if _linkedin_obscura_manager is None:
        _linkedin_obscura_manager = LinkedInObscuraManager()
    return _linkedin_obscura_manager


async def get_valid_linkedin_cookies(force_refresh: bool = False) -> CookieValidationResult:
    """Get valid LinkedIn cookies using ObscuraCookieManager."""
    manager = get_linkedin_obscura_manager()
    return await manager.get_valid_cookies(force_refresh)


async def force_linkedin_cookie_refresh() -> CookieValidationResult:
    """Force re-extraction of LinkedIn cookies from browser."""
    manager = get_linkedin_obscura_manager()
    return await manager.force_re_extraction()


async def invalidate_linkedin_auth() -> None:
    """Invalidate LinkedIn auth and trigger re-login."""
    manager = get_linkedin_obscura_manager()
    await manager.invalidate_and_trigger_relogin()