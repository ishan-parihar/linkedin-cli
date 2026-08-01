"""
LinkedIn-specific ObscuraCookieManager integration.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from obscura_core import (
    ObscuraCookieManager,
    FileCookieStorage,
    LinkedInCookieExtractor,
    CookieValidationResult,
)

from linkedin_mcp_server.session_state import portable_cookie_path

logger = logging.getLogger(__name__)

# Required cookies for LinkedIn
LINKEDIN_REQUIRED_COOKIES = ["li_at"]


class LinkedInCookieValidator:
    """Validates LinkedIn cookies by making an API call."""

    def __init__(self):
        self._extractor = None

    async def validate(self, cookies: dict[str, str]) -> bool:
        """Validate cookies by checking required cookies are present and performing browser validation if enabled."""
        try:
            # Fast fail: check that required cookies are present
            required = ["li_at"]
            for cookie in required:
                if cookie not in cookies or not cookies[cookie]:
                    logger.debug(f"Required cookie missing: {cookie}")
                    return False

            # Full browser validation can be disabled for resource-constrained environments
            # Set LINKEDIN_SKIP_BROWSER_VALIDATION=1 to skip browser-based validation
            skip_browser_validation = os.getenv("LINKEDIN_SKIP_BROWSER_VALIDATION", "").lower() in (
                "1", "true", "yes", "on"
            )

            if skip_browser_validation:
                logger.debug("Skipping browser-based validation (LINKEDIN_SKIP_BROWSER_VALIDATION set)")
                return True

            # Import here to avoid circular imports
            from linkedin_mcp_server.drivers.browser import get_or_create_browser

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

            # Check if we're logged in (locale-independent check)
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
        return FileCookieStorage(portable_cookie_path())

    def _get_extractor(self) -> LinkedInCookieExtractor:
        """Get browser cookie extractor (prefers Chrome/Arc)."""
        return LinkedInCookieExtractor(preferred_browsers=["chrome", "arc", "brave", "firefox", "edge"])

    def _get_manager(self) -> ObscuraCookieManager:
        """Get or create the ObscuraCookieManager instance."""
        if self._manager is None:
            self._manager = ObscuraCookieManager(
                storage=self._get_storage(),
                extractor=self._get_extractor(),
                validator=self._validator.validate,
                required_cookies=LINKEDIN_REQUIRED_COOKIES,
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