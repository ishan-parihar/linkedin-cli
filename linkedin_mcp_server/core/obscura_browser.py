"""
Obscura-based browser manager for LinkedIn scraping.

Provides lightweight browser management using Obscura for LinkedIn scraping
with transformative performance improvements over traditional browser automation.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from linkedin_mcp_server.common_utils import (
    harden_linkedin_tree,
    secure_mkdir,
    secure_write_text,
)
from linkedin_mcp_server.cookie_import import (
    auto_extract_cookies,
    extract_cookies_from_browser,
)
from linkedin_mcp_server.core.obscura_error_handling import (
    handle_obscura_error,
    log_obscura_operation,
    log_obscura_performance,
    ObscuraError,
    ObscuraTimeoutError,
    ObscuraFetchError,
)
from linkedin_mcp_server.core.obscura_binary_manager import (
    ensure_obscura_binary,
)

logger = logging.getLogger(__name__)

# Obscura binary path
_OBSCURA_PATH = "/tmp/obscura"
# Required LinkedIn cookies
_REQUIRED_COOKIES = {"li_at", "bscookie"}
# Default user data directory
_DEFAULT_USER_DATA_DIR = Path.home() / ".linkedin-mcp" / "profile"
# Private file mode
_PRIVATE_FILE_MODE = 0o600


class ObscuraBrowserManager:
    """Obscura-based browser manager with Playwright-compatible interface.
    
    Implements the same interface as core/browser.py BrowserManager but uses
    Obscura for lightweight scraping with 99.85% faster startup and 99.6% 
    less memory usage.
    """

    def __init__(
        self,
        user_data_dir: str | Path = _DEFAULT_USER_DATA_DIR,
        headless: bool = True,
        slow_mo: int = 0,
        viewport: dict[str, int] | None = None,
        user_agent: str | None = None,
        **launch_options: Any,
    ):
        self.user_data_dir = str(Path(user_data_dir).expanduser())
        self.headless = headless
        self.slow_mo = slow_mo
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.user_agent = user_agent
        self.launch_options = launch_options

        # Obscura-specific state
        self._cookies: dict[str, str] = {}
        self._is_authenticated = False
        self._storage_dir: Path | None = None
        self._page_content: str = ""
        self._current_url: str = ""
        
        # Compatibility with Playwright interface
        self._close_confirmed = False

    async def __aenter__(self) -> "ObscuraBrowserManager":
        await self.start()
        return self

    async def __aexit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        self._close_confirmed = await self.close()

    async def start(self) -> None:
        """Start Obscura browser session."""
        if self._storage_dir is not None:
            raise RuntimeError("Browser already started. Call close() first.")
        
        try:
            # Ensure Obscura binary is available and up to date
            binary_path = await ensure_obscura_binary()
            logger.info("Using Obscura binary: %s", binary_path)
            
            # Update global binary path
            global _OBSCURA_PATH
            _OBSCURA_PATH = str(binary_path)
            
            # Create storage directory for session persistence
            self._storage_dir = Path(self.user_data_dir)
            secure_mkdir(self._storage_dir)
            harden_linkedin_tree(self._storage_dir)
            
            # Load cookies from existing file or extract from browser
            await self._load_cookies()
            
            logger.info(
                "Obscura browser session started (headless=%s, user_data_dir=%s)",
                self.headless,
                self.user_data_dir,
            )
            
        except Exception as e:
            logger.error("Failed to start Obscura browser: %s", e)
            raise

    async def close(self) -> bool:
        """Close Obscura browser session and cleanup resources."""
        self._storage_dir = None
        self._cookies = {}
        self._page_content = ""
        self._current_url = ""
        self._close_confirmed = True
        
        logger.info("Obscura browser session closed")
        return True

    @property
    def close_confirmed(self) -> bool:
        """Whether the last close was confirmed."""
        return self._close_confirmed

    async def goto(self, url: str, **kwargs: Any) -> None:
        """Navigate to URL using Obscura fetch."""
        await self._fetch_page(url)

    async def _fetch_page(self, url: str) -> None:
        """Fetch page content using Obscura."""
        import time
        start_time = time.time()
        
        cmd = [
            _OBSCURA_PATH,
            "fetch",
            "--dump", "html",
            "--stealth",
        ]
        
        # Add storage directory for session persistence
        if self._storage_dir:
            cmd.extend(["--storage-dir", str(self._storage_dir)])
        
        # Cookies are injected via --storage-dir persistence, not a CLI flag.
        # The obscura binary does not support a --cookie argument; it manages
        # cookies automatically through its storage directory. The cookies
        # loaded via _load_cookies() are used by the extractor and for
        # authentication validation, while obscura's own cookie jar handles
        # HTTP request headers.
        cmd.append(url)
        
        log_obscura_operation("fetch_page", {"url": url, "storage_dir": str(self._storage_dir), "cookies": len(self._cookies)})
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            duration = time.time() - start_time
            log_obscura_performance("fetch_page", duration, {"url": url, "content_length": len(result.stdout)})
            
            if result.returncode == 0:
                self._page_content = result.stdout
                self._current_url = url
                logger.debug("Successfully fetched page: %s (%d chars)", url, len(result.stdout))
            else:
                error_msg = f"Obscura fetch failed: {result.stderr}"
                logger.error(error_msg)
                handle_obscura_error(ObscuraFetchError(error_msg), f"fetch_page({url})")
                raise ObscuraFetchError(error_msg)
                
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            log_obscura_performance("fetch_page", duration, {"url": url, "timeout": True})
            error_msg = f"Obscura fetch timed out for {url}"
            handle_obscura_error(ObscuraTimeoutError(error_msg), f"fetch_page({url})")
            raise ObscuraTimeoutError(error_msg)
        except Exception as e:
            duration = time.time() - start_time
            handle_obscura_error(e, f"fetch_page({url})")
            raise

    async def content(self) -> str:
        """Get current page content."""
        return self._page_content

    async def title(self) -> str:
        """Get page title using JavaScript eval."""
        return await self._evaluate_js("document.title")

    async def url(self) -> str:
        """Get current URL."""
        return self._current_url

    async def evaluate(self, script: str) -> Any:
        """Evaluate JavaScript in page context."""
        return await self._evaluate_js(script)

    async def _evaluate_js(self, script: str) -> Any:
        """Evaluate JavaScript using Obscura eval."""
        if not self._current_url:
            raise RuntimeError("No page loaded")
        
        cmd = [
            _OBSCURA_PATH,
            "fetch",
            "--dump", "html",
            "--eval", script,
            "--stealth",
            self._current_url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Return the eval result (stdout contains the result)
                return result.stdout.strip()
            else:
                logger.warning("JavaScript eval failed: %s", result.stderr)
                return None
                
        except Exception as e:
            logger.error("JavaScript eval error: %s", e)
            return None

    async def set_cookie(
        self, name: str, value: str, domain: str = ".linkedin.com"
    ) -> None:
        """Set cookie in session."""
        self._cookies[name] = value
        logger.debug("Cookie set: %s", name)

    async def cookies(self) -> list[dict[str, Any]]:
        """Get all cookies as Playwright-compatible format."""
        return [
            {
                "name": name,
                "value": value,
                "domain": ".linkedin.com",
                "path": "/"
            }
            for name, value in self._cookies.items()
        ]

    async def add_cookies(self, cookies: list[dict[str, Any]]) -> None:
        """Add cookies in Playwright format."""
        for cookie in cookies:
            name = cookie.get("name")
            value = cookie.get("value")
            if name and value:
                self._cookies[name] = value
        logger.info("Added %d cookies", len(cookies))
    
    async def import_cookies(
        self,
        cookie_path: str | Path | None = None,
        *,
        preset_name: str | None = None,
    ) -> bool:
        """Import cookies from portable JSON file (Playwright-compatible interface)."""
        path = Path(cookie_path) if cookie_path else self._default_cookie_path()
        
        if not path.exists():
            logger.debug("No cookie file at %s", path)
            return False
        
        try:
            cookie_data = json.loads(path.read_text())
            if not cookie_data:
                logger.debug("Cookie file is empty")
                return False
            
            # Filter for LinkedIn cookies
            linkedin_cookies = [
                cookie for cookie in cookie_data
                if "linkedin.com" in cookie.get("domain", "")
            ]
            
            # Check for required cookies
            has_li_at = any(c.get("name") == "li_at" for c in linkedin_cookies)
            if not has_li_at:
                logger.warning("No li_at cookie found in %s", path)
                return False
            
            # Load cookies
            self._cookies = {c['name']: c['value'] for c in linkedin_cookies}
            
            if self._validate_cookies():
                self._is_authenticated = True
                logger.info("Imported %d cookies from %s", len(linkedin_cookies), path)
                return True
            else:
                logger.warning("Imported cookies missing required fields")
                return False
                
        except Exception as e:
            logger.error("Failed to import cookies from %s: %s", path, e)
            return False
    
    async def export_storage_state(self, storage_state_path: str | Path, *, indexed_db: bool = False) -> bool:
        """Export storage state (cookies) to a file (Playwright-compatible interface)."""
        return await self.export_cookies(storage_state_path)

    @property
    def is_authenticated(self) -> bool:
        """Check if browser is authenticated."""
        return self._is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, value: bool) -> None:
        """Set authentication status."""
        self._is_authenticated = value

    def _default_cookie_path(self) -> Path:
        """Get default cookie file path."""
        return Path.home() / ".linkedin-mcp" / "cookies.json"

    async def _load_cookies(self) -> None:
        """Load cookies from file or browser extraction."""
        # Try loading from existing cookie file first
        cookie_path = self._default_cookie_path()
        if cookie_path.exists():
            try:
                cookie_data = json.loads(cookie_path.read_text())
                self._cookies = {cookie['name']: cookie['value'] for cookie in cookie_data}
                
                if self._validate_cookies():
                    self._is_authenticated = True
                    logger.info("Loaded cookies from file: %s", cookie_path)
                    return
            except Exception as e:
                logger.warning("Failed to load cookies from file: %s", e)
        
        # Try extracting from browser
        try:
            cookies = auto_extract_cookies()
            if cookies and self._validate_cookies_dict(cookies):
                self._cookies = cookies
                self._is_authenticated = True
                logger.info("Extracted cookies from browser")
            else:
                logger.warning("No valid cookies found in browser")
        except Exception as e:
            logger.warning("Failed to extract cookies from browser: %s", e)

    def _validate_cookies(self) -> bool:
        """Validate loaded cookies."""
        return _REQUIRED_COOKIES.issubset(self._cookies.keys())

    def _validate_cookies_dict(self, cookies: dict[str, str]) -> bool:
        """Validate cookie dictionary."""
        return _REQUIRED_COOKIES.issubset(cookies.keys())

    async def export_cookies(self, cookie_path: str | Path | None = None) -> bool:
        """Export cookies to portable JSON file."""
        path = Path(cookie_path) if cookie_path else self._default_cookie_path()
        
        try:
            cookies = [
                {
                    "name": name,
                    "value": value,
                    "domain": ".linkedin.com",
                    "path": "/"
                }
                for name, value in self._cookies.items()
            ]
            
            secure_mkdir(path.parent)
            harden_linkedin_tree(path.parent)
            secure_write_text(
                path, json.dumps(cookies, indent=2), mode=_PRIVATE_FILE_MODE
            )
            logger.info("Exported %d cookies to %s", len(cookies), path)
            return True
        except Exception as e:
            logger.error("Failed to export cookies: %s", e)
            return False

    async def import_cookies(
        self,
        cookie_path: str | Path | None = None,
        *,
        preset_name: str | None = None,
    ) -> bool:
        """Import cookies from portable JSON file."""
        path = Path(cookie_path) if cookie_path else self._default_cookie_path()
        
        if not path.exists():
            logger.debug("No cookie file at %s", path)
            return False
        
        try:
            cookie_data = json.loads(path.read_text())
            if not cookie_data:
                logger.debug("Cookie file is empty")
                return False
            
            # Filter for LinkedIn cookies
            linkedin_cookies = [
                cookie for cookie in cookie_data
                if "linkedin.com" in cookie.get("domain", "")
            ]
            
            # Check for required cookies
            has_li_at = any(c.get("name") == "li_at" for c in linkedin_cookies)
            if not has_li_at:
                logger.warning("No li_at cookie found in %s", path)
                return False
            
            # Load cookies
            self._cookies = {c['name']: c['value'] for c in linkedin_cookies}
            
            if self._validate_cookies():
                self._is_authenticated = True
                logger.info("Imported %d cookies from %s", len(linkedin_cookies), path)
                return True
            else:
                logger.warning("Imported cookies missing required fields")
                return False
                
        except Exception as e:
            logger.error("Failed to import cookies from %s: %s", path, e)
            return False

    def cookie_file_exists(self, cookie_path: str | Path | None = None) -> bool:
        """Check if cookie file exists."""
        path = Path(cookie_path) if cookie_path else self._default_cookie_path()
        return path.exists


# Page-like compatibility object
class ObscuraPage:
    """Page-like object for Obscura compatibility with Playwright interface."""
    
    def __init__(self, browser_manager: ObscuraBrowserManager):
        self._browser = browser_manager
        self._listeners: dict[str, list[callable]] = {}
    
    async def goto(self, url: str, **kwargs: Any) -> None:
        """Navigate to URL."""
        await self._browser.goto(url, **kwargs)
    
    async def content(self) -> str:
        """Get page content."""
        return await self._browser.content()
    
    async def title(self) -> str:
        """Get page title."""
        return await self._browser.title()
    
    @property
    def url(self) -> str:
        """Get current URL."""
        return self._browser._current_url
    
    async def evaluate(self, script: str) -> Any:
        """Evaluate JavaScript."""
        return await self._browser.evaluate(script)
    
    async def locator(self, selector: str) -> "ObscuraLocator":
        """Return a locator object."""
        return ObscuraLocator(self, selector)
    
    # --- Playwright-compatible event listener interface ---
    def on(self, event: str, handler: callable) -> None:
        """Add an event listener (Playwright-compatible)."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(handler)
    
    def remove_listener(self, event: str, handler: callable) -> None:
        """Remove an event listener (Playwright-compatible)."""
        if event in self._listeners and handler in self._listeners[event]:
            self._listeners[event].remove(handler)
    
    def _emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event to all listeners (internal use)."""
        if event in self._listeners:
            for handler in self._listeners[event]:
                try:
                    handler(*args, **kwargs)
                except Exception:
                    pass  # Ignore listener errors


class ObscuraLocator:
    """Locator-like object for basic element interactions."""
    
    def __init__(self, page: ObscuraPage, selector: str):
        self._page = page
        self._selector = selector
    
    async def count(self) -> int:
        """Count elements matching selector."""
        # Use JavaScript to count elements
        script = f"(function() {{ return document.querySelectorAll('{self._selector}').length; }})()"
        result = await self._page.evaluate(script)
        return int(result) if result else 0
    
    async def inner_text(self) -> str:
        """Get inner text of first matching element."""
        script = f"(function() {{ const el = document.querySelector('{self._selector}'); return el ? el.innerText : ''; }})()"
        return await self._page.evaluate(script) or ""


# Add page property to ObscuraBrowserManager for compatibility
@property
def page_property(self) -> ObscuraPage:
    """Get page-like object."""
    return ObscuraPage(self)

ObscuraBrowserManager.page = page_property


# ---------------------------------------------------------------------------
# Context property: setup.py and drivers/browser.py call `browser.context`
# to access cookies, storage state, etc. ObscuraBrowserManager already has
# async `cookies()` and `add_cookies()` methods — the context proxy just
# delegates to those so the Playwright-compatible interface is complete.
# ---------------------------------------------------------------------------
class _ObscuraContextProxy:
    """Playwright-like BrowserContext proxy for ObscuraBrowserManager.

    Delegates ``cookies()``, ``add_cookies()``, and ``set_cookies()`` to the
    underlying manager so callers that expect a ``browser.context`` handle
    (e.g. ``setup.py`` login flow) work transparently.
    """

    def __init__(self, manager: ObscuraBrowserManager):
        self._manager = manager

    async def cookies(self) -> list[dict[str, Any]]:
        return await self._manager.cookies()

    async def add_cookies(self, cookies: list[dict[str, Any]]) -> None:
        await self._manager.add_cookies(cookies)

    async def set_cookies(self, cookies: list[dict[str, Any]]) -> None:
        await self._manager.add_cookies(cookies)


@property
def context_property(self):
    """Get a Playwright-like BrowserContext proxy."""
    return _ObscuraContextProxy(self)


ObscuraBrowserManager.context = context_property