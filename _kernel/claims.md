# Claim Register

## Current Implementation Analysis
- Playwright (patchright) is used for browser lifecycle management via BrowserManager class — [V] — source: core/browser.py lines 11-16, 53-171 — unit 1
- Patchright provides persistent browser context with cookie/localStorage/session state retention — [V] — source: core/browser.py lines 56-59 — unit 1
- Current dependency includes patchright>=1.40.0 in pyproject.toml — [V] — source: pyproject.toml line 37 — unit 1
- Browser management uses singleton pattern with profile lease system — [V] — source: drivers/browser.py lines 61-71 — unit 1
- Extractor uses JavaScript execution for connection-state detection and action signals — [V] — source: scraping/extractor.py lines 287-336 — unit 2
- Multiple scraping sections map to specific LinkedIn URLs per fields.py — [V] — source: scraping/fields.py lines 8-26 — unit 2

## JavaScript Dependencies
- Connection state detection requires JavaScript execution — [V] — source: scraping/extractor.js lines 287-336 — unit 2
- Dynamic content hydration requires JavaScript wait functions — [V] — source: scraping/extractor.py lines 1512-1554 — unit 2
- Complex interactions (More button, incoming accept) require JavaScript — [V] — source: scraping/extractor.py lines 344-382 — unit 2
- Messaging compose interface requires JavaScript execution — [V] — source: scraping/extractor.py lines 4145-4184 — unit 2

## httpx Test Results
- httpx cannot handle LinkedIn's JavaScript redirects — [V] — source: test_httpx_static.py execution — unit 4
- LinkedIn blocks HTTP-only requests with 999 status and JavaScript redirect — [V] — source: /tmp/httpx_linkedin_sample.html — unit 4
- Authenticated requests with cookies still get 429 rate limiting — [V] — source: test_httpx_static.py execution — unit 4
- httpx/curlffi are not viable for LinkedIn scraping — [V] — source: httpx test analysis — unit 4

## Lightweight Browser Research
- Obscura provides Playwright-compatible CDP interface — [V] — source: Obscura README.md — unit 5
- Obscura has built-in anti-detection features — [V] — source: Obscura README.md — unit 5
- Obscura achieves 7x memory reduction vs Chrome — [V] — source: Obscura README.md — unit 5
- Lightpanda provides native MCP server support — [V] — source: Lightpanda README.md — unit 6
- Lightpanda achieves 16x memory reduction vs Chrome — [V] — source: Lightpanda README.md — unit 6
- Lightpanda is in beta status with missing CORS support — [V] — source: Lightpanda README.md — unit 6

## Authentication Complexity
- LinkedIn requires JavaScript for basic navigation — [V] — source: httpx test results — unit 3
- Session management depends on persistent browser context — [V] — source: core/browser.py lines 56-59 — unit 3
- Cookie import/export requires browser APIs — [V] — source: core/browser.py lines 286-446 — unit 3
- Storage state checkpointing needs IndexedDB support — [V] — source: drivers/browser.py lines 454-457 — unit 3
