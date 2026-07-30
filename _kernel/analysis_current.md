# Current Implementation Analysis

## Playwright Usage Summary

### Core Dependencies
- **patchright>=1.40.0** (pyproject.toml line 37)
- **BrowserManager** class (core/browser.py) - persistent browser context lifecycle
- **Singleton pattern** with profile lease system (drivers/browser.py)

### JavaScript Execution Requirements

#### Critical JS Dependencies (cannot work without JS execution):
1. **Connection State Detection** (_ACTION_SIGNALS_JS, lines 287-336)
   - Locale-independent detection of invite/compose/edit-intro signals
   - Action root finding via DOM traversal
   - Incoming request fingerprinting

2. **Dynamic Content Hydration** (wait_for_function calls throughout extractor.py)
   - Search results pages load placeholder then fill via JS
   - Company people pages hydrate employee listings after load
   - Details sections experience delayed content rendering
   - Feed infinite scroll pagination

3. **Complex Interactions**
   - More button opening (_OPEN_MORE_BUTTON_JS)
   - Incoming request accept (_CLICK_INCOMING_ACCEPT_JS)
   - Messaging compose interface interaction
   - Dialog/modal handling

4. **Data Extraction**
   - innerText extraction via page.evaluate()
   - Sidebar data extraction (complex DOM queries)
   - Link metadata extraction from dynamic content

### Static Content (potentially HTTP-only):
- Basic profile sections (main profile, experience, education)
- Company about pages
- Simple listings where content is server-rendered

### Session Management Complexity
- Persistent browser context with cookie/localStorage/session state
- Cookie import/export for portable authentication
- Storage state checkpointing for Docker scenarios
- Profile lease system for concurrent access prevention

## Assessment for Lightweight Alternatives

### httpx/curlffi (HTTP-only)
**Pros:**
- Extremely lightweight
- Fast for static content
- No browser overhead

**Cons:**
- Cannot execute JavaScript
- Cannot handle dynamic content hydration
- Cannot perform complex interactions (clicks, modal handling)
- Limited session management (manual cookie handling only)
- Cannot handle LinkedIn's anti-bot protections that require JS execution

**Verdict:** Suitable only for basic static profile sections, insufficient for full functionality.

### obscura/lightpanda (lightweight browsers)
**Pros:**
- JavaScript execution capability
- Lighter than full Playwright
- Can handle dynamic content
- Can perform interactions

**Cons:**
- May lack Playwright's advanced features (persistent contexts, device emulation)
- Unknown stability with LinkedIn's complex UI
- Session management may be less mature
- Community and documentation smaller than Playwright

**Verdict:** Potential candidates, but require extensive testing and adaptation.

## Key Challenges
1. LinkedIn relies heavily on client-side rendering
2. Complex JavaScript-based interactions for core features
3. Anti-bot protections may require full browser capabilities
4. Session persistence and portability is critical
5. Locale-independent detection requires DOM access
