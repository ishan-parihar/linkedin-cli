"""
Lightweight browser manager for LinkedIn MCP Server (Playwright-free).

Uses Obscura and Lightpanda for lightweight LinkedIn scraping without
the heavy Playwright/Patchright dependency.
"""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from linkedin_mcp_server.cookie_import import (
    auto_extract_cookies,
    extract_cookies_from_browser,
    find_browser_cookie_db,
)

logger = logging.getLogger(__name__)

# Required LinkedIn cookies
REQUIRED_COOKIES = {"li_at", "bscookie"}


class LightweightCookieManager:
    """Manage cookies for lightweight browsers."""

    def __init__(self):
        self.cached_cookies = None
        self.cookie_source = None

    def extract_cookies(self, browser_id: str | None = None) -> dict[str, str] | None:
        """Extract cookies from browser or auto-detect."""
        if browser_id:
            cookies = extract_cookies_from_browser(browser_id)
            self.cookie_source = browser_id
        else:
            cookies = auto_extract_cookies()
            self.cookie_source = "auto-detected"
        
        if cookies:
            self.cached_cookies = cookies
            logger.info(f"Extracted cookies from {self.cookie_source}: {list(cookies.keys())}")
        else:
            logger.warning("No cookies extracted")
        
        return cookies

    def validate_cookies(self, cookies: dict[str, str]) -> bool:
        """Validate that cookies contain required LinkedIn auth tokens."""
        if not cookies:
            return False
        return REQUIRED_COOKIES.issubset(cookies.keys())

    def format_cookie_string(self, cookies: dict[str, str]) -> str:
        """Format cookies as a string for HTTP headers."""
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])

    def load_from_file(self, cookie_path: Path) -> dict[str, str] | None:
        """Load cookies from JSON file (existing format)."""
        if not cookie_path.exists():
            return None
        
        try:
            cookie_data = json.loads(cookie_path.read_text())
            cookies = {cookie['name']: cookie['value'] for cookie in cookie_data}
            
            if self.validate_cookies(cookies):
                self.cached_cookies = cookies
                self.cookie_source = str(cookie_path)
                logger.info(f"Loaded cookies from {cookie_path}: {list(cookies.keys())}")
                return cookies
            else:
                logger.warning(f"Invalid cookies in {cookie_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading cookies from {cookie_path}: {e}")
            return None

    def get_cookies(self) -> dict[str, str]:
        """Get cached cookies or extract fresh ones."""
        if self.cached_cookies and self.validate_cookies(self.cached_cookies):
            return self.cached_cookies
        
        # Try to load from existing file first
        existing_cookies = self.load_from_file(Path.home() / ".linkedin-lyr" / "cookies.json")
        if existing_cookies:
            return existing_cookies
        
        # Extract from browser
        cookies = self.extract_cookies()
        if cookies and self.validate_cookies(cookies):
            return cookies
        
        raise Exception("No valid LinkedIn cookies available")


class LightweightBrowserManager:
    """Manage lightweight browser processes."""

    def __init__(self, preferred_browser: Literal["obscura", "lightpanda"] = "obscura"):
        self.preferred_browser = preferred_browser
        self.active_processes = {}
        self.cookie_manager = LightweightCookieManager()

    def start_obscura(self, port: int = 9222) -> subprocess.Popen:
        """Start Obscura in serve mode."""
        cmd = ["/tmp/obscura", "serve", "--stealth", "--port", str(port)]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.active_processes["obscura"] = process
        logger.info(f"Started Obscura on port {port}")
        return process

    def start_lightpanda(self, port: int = 9223) -> subprocess.Popen:
        """Start Lightpanda in serve mode."""
        cmd = ["/tmp/lightpanda", "serve", "--host", "127.0.0.1", "--port", str(port)]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.active_processes["lightpanda"] = process
        logger.info(f"Started Lightpanda on port {port}")
        return process

    def stop_all(self):
        """Stop all active browser processes."""
        for name, process in self.active_processes.items():
            logger.info(f"Stopping {name}")
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
        self.active_processes.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_all()


class LightweightContentFetcher:
    """Fetch LinkedIn content using lightweight browsers."""

    def __init__(self, browser_manager: LightweightBrowserManager):
        self.browser_manager = browser_manager
        self.cookie_manager = browser_manager.cookie_manager

    def fetch_with_obscura(self, url: str, cookies: dict[str, str] | None = None) -> str:
        """Fetch content using Obscura native fetch."""
        if cookies is None:
            cookies = self.cookie_manager.get_cookies()
        
        cmd = [
            "/tmp/obscura",
            "fetch",
            "--dump", "html",
            "--stealth",
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"Obscura fetch failed: {result.stderr}")

    def fetch_with_lightpanda(self, url: str, cookies: dict[str, str] | None = None) -> str:
        """Fetch content using Lightpanda native fetch."""
        if cookies is None:
            cookies = self.cookie_manager.get_cookies()
        
        cmd = [
            "/tmp/lightpanda",
            "fetch",
            "--dump", "html",
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"Lightpanda fetch failed: {result.stderr}")

    def fetch_with_storage(self, browser: str, url: str) -> str:
        """Fetch using browser storage with cookie persistence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir)
            
            # Try to use storage for cookie persistence
            # This is more complex and may require manual cookie setting
            if browser == "obscura":
                return self.fetch_with_obscura(url)
            elif browser == "lightpanda":
                return self.fetch_with_lightpanda(url)
            else:
                raise ValueError(f"Unknown browser: {browser}")

    def fetch_with_fallback(self, url: str) -> str:
        """Try multiple methods to fetch content."""
        # Try Obscura first
        try:
            logger.info("Trying Obscura...")
            return self.fetch_with_obscura(url)
        except Exception as e:
            logger.warning(f"Obscura failed: {e}")
        
        # Try Lightpanda
        try:
            logger.info("Trying Lightpanda...")
            return self.fetch_with_lightpanda(url)
        except Exception as e:
            logger.warning(f"Lightpanda failed: {e}")
        
        raise Exception("All fetch methods failed")


class LightweightLinkedInScraper:
    """LinkedIn scraper using lightweight browsers only."""

    def __init__(self, preferred_browser: Literal["obscura", "lightpanda"] = "obscura"):
        self.browser_manager = LightweightBrowserManager(preferred_browser)
        self.content_fetcher = LightweightContentFetcher(self.browser_manager)
        self.authenticated = False

    def authenticate(self, browser_id: str | None = None):
        """Authenticate by extracting cookies from real browser."""
        cookies = self.content_fetcher.cookie_manager.extract_cookies(browser_id)
        if cookies and self.content_fetcher.cookie_manager.validate_cookies(cookies):
            self.authenticated = True
            logger.info("Successfully authenticated with LinkedIn cookies")
        else:
            raise Exception("Failed to extract valid LinkedIn cookies")

    def get_profile(self, linkedin_username: str) -> dict:
        """Get LinkedIn profile using lightweight browser."""
        url = f"https://www.linkedin.com/in/{linkedin_username}/"
        
        try:
            html = self.content_fetcher.fetch_with_fallback(url)
            return self._parse_profile(html, url)
        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}")
            raise

    def get_company(self, company_id: str) -> dict:
        """Get LinkedIn company using lightweight browser."""
        url = f"https://www.linkedin.com/company/{company_id}/"
        
        try:
            html = self.content_fetcher.fetch_with_fallback(url)
            return self._parse_company(html, url)
        except Exception as e:
            logger.error(f"Failed to fetch company: {e}")
            raise

    def _parse_profile(self, html: str, url: str) -> dict:
        """Parse LinkedIn profile from HTML."""
        # Basic parsing - this needs to be expanded
        # For now, return the raw HTML with metadata
        return {
            "url": url,
            "html": html,
            "raw_text": html[:1000],  # Sample for now
            "auth_status": self._check_auth_status(html)
        }

    def _parse_company(self, html: str, url: str) -> dict:
        """Parse LinkedIn company from HTML."""
        # Basic parsing - this needs to be expanded
        return {
            "url": url,
            "html": html,
            "raw_text": html[:1000],  # Sample for now
            "auth_status": self._check_auth_status(html)
        }

    def _check_auth_status(self, html: str) -> str:
        """Check if HTML shows authentication barrier."""
        if "sign in" in html.lower() or "login" in html.lower():
            return "authentication_required"
        elif "feed" in html.lower() or "linkedin" in html.lower():
            return "authenticated"
        else:
            return "unknown"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser_manager.stop_all()


# Convenience function for quick usage
def create_lightweight_scraper(browser: Literal["obscura", "lightpanda"] = "obscura") -> LightweightLinkedInScraper:
    """Create a lightweight LinkedIn scraper."""
    return LightweightLinkedInScraper(browser)
