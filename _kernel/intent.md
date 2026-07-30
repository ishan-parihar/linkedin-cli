# Intent Table

## Deliverable
Investigation report and upgrade plan for replacing Playwright with lightweight alternatives (httpx, curlffi, obscura, lightpanda) in the linkedin-mcp-server.

## Constraints (ranked)
C1: Must not use heavy Playwright dependencies (primary requirement)
C2: Must maintain existing LinkedIn scraping functionality
C3: Must support authenticated sessions and LinkedIn's anti-bot protections
C4: Must pass existing test suite
C5: Must maintain locale-independent detection logic per CLAUDE.md rules
C6: Should minimize DOM dependence and prefer innerText/URL navigation

## Scope Fences
S1: Focus on linkedin-mcp-server codebase only
S2: Test alternatives against real LinkedIn (not just code analysis)
S3: Consider Python-native solutions (httpx, curlffi) and lightweight browsers (obscura, lightpanda)
S4: Preserve existing tool interface and return format
S5: Must work with existing MCP server architecture

## Literal vs Actual Divergence Checks
D1: User said "test and brainstorm" - actual requirement is systematic technical evaluation with working code
D2: User mentioned specific libraries - actual requirement is finding the best solution, not just testing those
D3: User said "upgrade it" - actual requirement is a phased migration plan with fallback strategy

## Assumptions
A1: Current Playwright implementation works but is too heavy
A2: LinkedIn scraping requires JavaScript execution for some features
A3: Session authentication can be preserved across implementations
A4: MCP server interface should remain stable for users
