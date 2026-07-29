"""AXI output utilities: truncation and next-step hints for MCP tool responses."""

from __future__ import annotations

from typing import Any

# AXI §3: default truncation limit for large text fields
_TRUNCATION_LIMIT = 500


def truncate_section_text(text: str, limit: int = _TRUNCATION_LIMIT, *, full: bool = False) -> str:
    """Truncate a section's raw_text to *limit* chars unless *full* is set.

    Returns the original text when under the limit or when full=True.
    """
    if full or len(text) <= limit:
        return text
    return f"{text[:limit]}... (truncated, {len(text)} chars total)"


def apply_section_truncation(
    sections: dict[str, str],
    limit: int = _TRUNCATION_LIMIT,
    *,
    full: bool = False,
) -> dict[str, str]:
    """Truncate all values in a sections dict. Returns a new dict."""
    if full:
        return sections
    return {k: truncate_section_text(v, limit) for k, v in sections.items()}


def add_next_step(result: dict[str, Any], hints: list[str]) -> dict[str, Any]:
    """Append a help[] next-step hint list to a tool result dict. Returns the same dict."""
    if hints:
        result["help"] = hints
    return result


# Per-tool next-step hint maps (AXI §9)
PERSON_PROFILE_HINTS = [
    "Use sections='posts,skills' to get specific sections",
    "Use max_scrolls=5 for deeper profile scraping",
]

SEARCH_PEOPLE_HINTS = [
    "Use network=['1st'] to filter by connection degree",
    "Use current_company to filter by employer",
]

FEED_HINTS = [
    "Use num_posts=50 for the maximum feed snapshot",
    "Each entry includes kind:'feed_post' references for follow-up",
]

SEARCH_POSTS_HINTS = [
    "Use date_posted='pastWeek' to narrow results",
    "Use max_pages=10 for broader search coverage",
]

COMPANY_HINTS = [
    "Use sections='about,staff' to get specific sections",
    "Use max_scrolls for deeper company scraping",
]

JOB_HINTS = [
    "Use keywords and location to narrow search",
    "get_saved_jobs retrieves your saved job list",
]
