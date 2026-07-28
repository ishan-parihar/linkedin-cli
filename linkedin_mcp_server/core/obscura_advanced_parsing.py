"""
Advanced content parsing using JavaScript eval for Obscura.

Provides JavaScript-based content extraction for LinkedIn pages to handle
dynamic content and complex data structures that static HTML parsing cannot handle.
"""

import logging
import json
from typing import Any, Optional, Dict, List
import re

from linkedin_mcp_server.core.feature_flags import is_obscura_advanced_feature_enabled

logger = logging.getLogger(__name__)


class LinkedInJavaScriptParser:
    """JavaScript-based parser for LinkedIn content extraction."""
    
    def __init__(self, obscura_browser):
        self.obscura_browser = obscura_browser
        self._parse_cache: dict = {}
    
    async def extract_profile_data(self, url: str) -> Dict[str, Any]:
        """Extract LinkedIn profile data using JavaScript."""
        if not is_obscura_advanced_feature_enabled("advanced_parsing"):
            return await self._basic_profile_extraction(url)
        
        try:
            # Navigate to profile page
            await self.obscura_browser.goto(url)
            
            # Use JavaScript to extract profile data
            profile_script = """
            (function() {
                try {
                    // Extract basic profile information
                    const nameElement = document.querySelector('h1');
                    const headlineElement = document.querySelector('.text-body-medium');
                    const locationElement = document.querySelector('.text-body-small.inline-show-more-text');
                    
                    // Extract experience section
                    const experienceSection = document.querySelector('#experience');
                    const experiences = [];
                    if (experienceSection) {
                        const experienceItems = experienceSection.querySelectorAll('.pvs-list__item--line-separated');
                        experienceItems.forEach(item => {
                            const title = item.querySelector('.t-bold')?.innerText || '';
                            const company = item.querySelector('.t-14')?.innerText || '';
                            if (title || company) {
                                experiences.push({ title, company });
                            }
                        });
                    }
                    
                    // Extract education section
                    const educationSection = document.querySelector('#education');
                    const education = [];
                    if (educationSection) {
                        const educationItems = educationSection.querySelectorAll('.pvs-list__item--line-separated');
                        educationItems.forEach(item => {
                            const school = item.querySelector('.t-bold')?.innerText || '';
                            const degree = item.querySelector('.t-14')?.innerText || '';
                            if (school || degree) {
                                education.push({ school, degree });
                            }
                        });
                    }
                    
                    return {
                        name: nameElement?.innerText || '',
                        headline: headlineElement?.innerText || '',
                        location: locationElement?.innerText || '',
                        experience: experiences,
                        education: education,
                        success: true
                    };
                } catch (e) {
                    return { success: false, error: e.toString() };
                }
            })()
            """
            
            result = await self.obscura_browser.evaluate(profile_script)
            
            if result and isinstance(result, str):
                try:
                    profile_data = json.loads(result)
                    if profile_data.get('success'):
                        logger.info("Successfully extracted profile data using JavaScript")
                        return profile_data
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JavaScript result as JSON")
            
            # Fallback to basic extraction
            return await self._basic_profile_extraction(url)
            
        except Exception as e:
            logger.error("JavaScript profile extraction failed: %s", e)
            return await self._basic_profile_extraction(url)
    
    async def extract_company_data(self, url: str) -> Dict[str, Any]:
        """Extract LinkedIn company data using JavaScript."""
        if not is_obscura_advanced_feature_enabled("advanced_parsing"):
            return await self._basic_company_extraction(url)
        
        try:
            await self.obscura_browser.goto(url)
            
            company_script = """
            (function() {
                try {
                    const nameElement = document.querySelector('h1');
                    const industryElement = document.querySelector('.text-body-medium');
                    const locationElement = document.querySelector('.text-body-small');
                    
                    // Extract company size
                    const sizeElement = document.querySelector('[aria-label*="Company size"]');
                    const size = sizeElement?.innerText || '';
                    
                    // Extract followers
                    const followersElement = document.querySelector('[aria-label*="followers"]');
                    const followers = followersElement?.innerText || '';
                    
                    return {
                        name: nameElement?.innerText || '',
                        industry: industryElement?.innerText || '',
                        location: locationElement?.innerText || '',
                        size: size,
                        followers: followers,
                        success: true
                    };
                } catch (e) {
                    return { success: false, error: e.toString() };
                }
            })()
            """
            
            result = await self.obscura_browser.evaluate(company_script)
            
            if result and isinstance(result, str):
                try:
                    company_data = json.loads(result)
                    if company_data.get('success'):
                        logger.info("Successfully extracted company data using JavaScript")
                        return company_data
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JavaScript result as JSON")
            
            return await self._basic_company_extraction(url)
            
        except Exception as e:
            logger.error("JavaScript company extraction failed: %s", e)
            return await self._basic_company_extraction(url)
    
    async def extract_feed_posts(self, url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Extract LinkedIn feed posts using JavaScript."""
        if not is_obscura_advanced_feature_enabled("advanced_parsing"):
            return await self._basic_feed_extraction(url, limit)
        
        try:
            await self.obscura_browser.goto(url)
            
            feed_script = f"""
            (function() {{
                try {{
                    const posts = [];
                    const postElements = document.querySelectorAll('.feed-shared-update-v2');
                    
                    for (let i = 0; i < Math.min({limit}, postElements.length); i++) {{
                        const post = postElements[i];
                        
                        const authorElement = post.querySelector('.feed-shared-actor__name');
                        const contentElement = post.querySelector('.feed-shared-text');
                        const likesElement = post.querySelector('[aria-label*="like"]');
                        const commentsElement = post.querySelector('[aria-label*="comment"]');
                        
                        posts.push({{
                            author: authorElement?.innerText || '',
                            content: contentElement?.innerText || '',
                            likes: likesElement?.innerText || '0',
                            comments: commentsElement?.innerText || '0',
                            success: true
                        }});
                    }}
                    
                    return {{ posts, success: true }};
                }} catch (e) {{
                    return {{ success: false, error: e.toString() }};
                }}
            }})()
            """
            
            result = await self.obscura_browser.evaluate(feed_script)
            
            if result and isinstance(result, str):
                try:
                    feed_data = json.loads(result)
                    if feed_data.get('success'):
                        logger.info("Successfully extracted %d feed posts using JavaScript", len(feed_data.get('posts', [])))
                        return feed_data.get('posts', [])
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JavaScript result as JSON")
            
            return await self._basic_feed_extraction(url, limit)
            
        except Exception as e:
            logger.error("JavaScript feed extraction failed: %s", e)
            return await self._basic_feed_extraction(url, limit)
    
    async def _basic_profile_extraction(self, url: str) -> Dict[str, Any]:
        """Basic profile extraction fallback."""
        await self.obscura_browser.goto(url)
        content = await self.obscura_browser.content()
        
        # Use regex for basic extraction
        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        headline_match = re.search(r'<[^>]*class="[^"]*text-body-medium[^"]*"[^>]*>([^<]+)</', content)
        
        return {
            "name": name_match.group(1).strip() if name_match else "",
            "headline": headline_match.group(1).strip() if headline_match else "",
            "location": "",
            "experience": [],
            "education": [],
            "extraction_method": "basic_regex"
        }
    
    async def _basic_company_extraction(self, url: str) -> Dict[str, Any]:
        """Basic company extraction fallback."""
        await self.obscura_browser.goto(url)
        content = await self.obscura_browser.content()
        
        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        
        return {
            "name": name_match.group(1).strip() if name_match else "",
            "industry": "",
            "location": "",
            "size": "",
            "followers": "",
            "extraction_method": "basic_regex"
        }
    
    async def _basic_feed_extraction(self, url: str, limit: int) -> List[Dict[str, Any]]:
        """Basic feed extraction fallback."""
        await self.obscura_browser.goto(url)
        content = await self.obscura_browser.content()
        
        # Count feed posts
        post_matches = re.findall(r'<[^>]*class="[^"]*feed-shared-update[^"]*"[^>]*>', content)
        
        return [
            {
                "author": "",
                "content": "",
                "likes": "0",
                "comments": "0",
                "extraction_method": "basic_count"
            }
            for _ in range(min(limit, len(post_matches)))
        ]
    
    async def check_page_loaded(self) -> bool:
        """Check if the page is fully loaded using JavaScript."""
        check_script = """
        (function() {
            return document.readyState === 'complete';
        })()
        """
        
        result = await self.obscura_browser.evaluate(check_script)
        return result == "true" if isinstance(result, str) else bool(result)
    
    async def wait_for_content(self, selector: str, timeout: int = 5000) -> bool:
        """Wait for a specific element to appear using JavaScript."""
        wait_script = f"""
        (function() {{
            return new Promise((resolve) => {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    resolve(true);
                }} else {{
                    setTimeout(() => {{
                        const el = document.querySelector('{selector}');
                        resolve(!!el);
                    }}, {timeout});
                }}
            }});
        }})()
        """
        
        result = await self.obscura_browser.evaluate(wait_script)
        return result == "true" if isinstance(result, str) else bool(result)
    
    async def extract_links(self, url_pattern: str = "linkedin.com") -> List[str]:
        """Extract all links matching a pattern from the current page."""
        links_script = f"""
        (function() {{
            const links = Array.from(document.querySelectorAll('a[href*="{url_pattern}"]'));
            return links.map(a => a.href);
        }})()
        """
        
        result = await self.obscura_browser.evaluate(links_script)
        
        if result and isinstance(result, str):
            try:
                links = json.loads(result)
                logger.info("Extracted %d links matching pattern", len(links))
                return links
            except json.JSONDecodeError:
                logger.warning("Failed to parse links result as JSON")
        
        return []
    
    def get_parse_stats(self) -> Dict[str, Any]:
        """Get parsing statistics."""
        return {
            "cache_size": len(self._parse_cache),
            "advanced_parsing_enabled": is_obscura_advanced_feature_enabled("advanced_parsing"),
        }


class DynamicContentExtractor:
    """Extract dynamic content that requires JavaScript execution."""
    
    def __init__(self, obscura_browser):
        self.obscura_browser = obscura_browser
        self._extraction_scripts: Dict[str, str] = {
            "scroll_height": "(function() { return document.body.scrollHeight; })()",
            "inner_height": "(function() { return window.innerHeight; })()",
            "element_count": "(function() { return document.querySelectorAll('*').length; })()",
            "is_loaded": "(function() { return document.readyState === 'complete'; })()",
        }
    
    async def extract_metric(self, metric_name: str) -> Any:
        """Extract a specific metric using JavaScript."""
        script = self._extraction_scripts.get(metric_name)
        if not script:
            logger.warning("Unknown metric: %s", metric_name)
            return None
        
        result = await self.obscura_browser.evaluate(script)
        logger.debug("Extracted metric %s: %s", metric_name, result)
        return result
    
    async def scroll_page(self, scroll_count: int = 3) -> None:
        """Scroll the page to trigger dynamic content loading."""
        for i in range(scroll_count):
            scroll_script = f"""
            (function() {{
                window.scrollTo(0, document.body.scrollHeight * {(i + 1) / scroll_count});
                return true;
            }})()
            """
            
            await self.obscura_browser.evaluate(scroll_script)
            
            # Wait for content to load
            import asyncio
            await asyncio.sleep(0.5)
        
        logger.info("Scrolled page %d times", scroll_count)
    
    async def trigger_infinite_scroll(self, max_scrolls: int = 5) -> int:
        """Trigger infinite scroll to load more content."""
        previous_height = 0
        scroll_count = 0
        
        for i in range(max_scrolls):
            current_height = await self.extract_metric("scroll_height")
            
            if current_height == previous_height:
                logger.info("No more content to load after %d scrolls", scroll_count)
                break
            
            await self.scroll_page(1)
            previous_height = current_height
            scroll_count += 1
        
        logger.info("Triggered infinite scroll: %d total scrolls", scroll_count)
        return scroll_count


# Global instances
_js_parser: LinkedInJavaScriptParser | None = None
_dynamic_extractor: DynamicContentExtractor | None = None


def get_js_parser(obscura_browser) -> LinkedInJavaScriptParser:
    """Get the JavaScript parser instance."""
    global _js_parser
    
    if _js_parser is None:
        _js_parser = LinkedInJavaScriptParser(obscura_browser)
    
    return _js_parser


def get_dynamic_extractor(obscura_browser) -> DynamicContentExtractor:
    """Get the dynamic content extractor instance."""
    global _dynamic_extractor
    
    if _dynamic_extractor is None:
        _dynamic_extractor = DynamicContentExtractor(obscura_browser)
    
    return _dynamic_extractor