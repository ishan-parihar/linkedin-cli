# LinkedIn MCP Server

Manage LinkedIn authentication, profiles, companies, and job data through your own browser session. Use when you need to access LinkedIn data like profiles, company information, job postings, or messaging through AI agents.

## When to Use

Use this skill when:
- You need to access LinkedIn profile data (person profiles, company profiles)
- You want to search for jobs or people on LinkedIn
- You need to interact with LinkedIn messaging
- You want to scrape LinkedIn feed data
- You need LinkedIn authentication for automated tasks

## Quick Start

### Check Session Status

```bash
linkedin-lyr status
```

### Import LinkedIn Session from Browser

```bash
# Auto-detect browser
linkedin-lyr import

# Specific browser
linkedin-lyr import brave
linkedin-lyr import chrome
linkedin-lyr import firefox
```

### Start MCP Server

```bash
linkedin-lyr mcp
```

## Available Commands

### `status` - Check Session Status

Show current LinkedIn authentication session status.

```bash
linkedin-lyr status          # Basic status
linkedin-lyr status --full   # Full details with cookie names
```

**Output fields:**
- `session`: Session status (none/active/invalid/error)
- `cookies`: Number of cookies stored
- `path`: Path to cookie storage file

### `browsers` - List Supported Browsers

List all supported browsers and their installation status.

```bash
linkedin-lyr browsers
```

**Output fields:**
- `id`: Browser identifier
- `name`: Browser display name
- `engine`: Browser engine (chromium/firefox)
- `installed`: Whether browser is installed
- `description`: Browser description

### `import [browser]` - Import LinkedIn Session

Import LinkedIn authentication cookies from your browser.

```bash
linkedin-lyr import           # Auto-detect browser
linkedin-lyr import brave    # Specific browser
linkedin-lyr import chrome   # Specific browser
```

**Output fields:**
- `status`: Import status (success/failed)
- `browser`: Browser used for import
- `cookies`: Number of cookies imported
- `path`: Path to saved cookie file
- `cookie_names`: Names of imported cookies

### `logout` - Clear Session

Clear stored LinkedIn authentication session.

```bash
linkedin-lyr logout
```

**Output fields:**
- `status`: Operation status (success/no-op)
- `message`: Status message

### `mcp [args...]` - Start MCP Server

Start the LinkedIn MCP server with optional arguments.

```bash
linkedin-lyr mcp                        # Start with defaults
linkedin-lyr mcp --transport stdio     # Specific transport
linkedin-lyr mcp --log-level DEBUG     # Debug logging
```

### `setup-session` - Install Session Hooks

Install session hooks for agent integrations (Claude Code, Codex).

```bash
linkedin-lyr setup-session
```

## Session Context

When properly integrated, agents receive live session context at startup:

```
bin: ~/.local/bin/linkedin-lyr
description: LinkedIn MCP Server - Manage LinkedIn authentication and scraping
session: valid (4 cookies)

help[2]:
  Run 'linkedin-lyr status' for session details
  Run 'linkedin-lyr mcp' to start the MCP server
```

## MCP Tools

Once authenticated, the MCP server provides these tools:

### Profile Tools
- `get_person_profile` - Get LinkedIn profile information
- `get_my_profile` - Get your own LinkedIn profile
- `connect_with_person` - Send connection requests

### Company Tools
- `get_company_profile` - Get company information
- `search_companies` - Search for companies
- `get_company_posts` - Get company posts
- `get_company_employees` - List company employees

### Job Tools
- `search_jobs` - Search for jobs
- `get_job_details` - Get job posting details
- `get_saved_jobs` - List saved jobs

### Messaging Tools
- `get_inbox` - List messaging conversations
- `get_conversation` - Read specific conversation
- `send_message` - Send messages

### Feed Tools
- `get_feed` - Get home feed posts
- `search_posts` - Search posts by keyword

## Configuration

### Environment Variables

- `LINKEDIN_USER_DATA_DIR` - Browser profile directory (default: ~/.linkedin/profile)
- `LINKEDIN_LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `LINKEDIN_HEADLESS` - Run browser headless (true/false)

### Cookie Storage

Cookies are stored in `~/.linkedin/cookies.json` in Obscura-compatible format.

## Troubleshooting

### Session Validation Failed

If session validation fails:
1. Re-import cookies: `linkedin-lyr import`
2. Ensure you're logged into LinkedIn in your browser
3. Try a different browser if encryption issues occur

### No Supported Browsers Found

If no browsers are detected:
1. Install a supported browser (Brave, Chrome, Firefox, Edge)
2. Ensure browser is in standard location
3. Check browser is not running in sandbox mode

### MCP Server Connection Issues

If MCP server fails to connect:
1. Check session status: `linkedin-lyr status`
2. Verify cookies are valid: `linkedin-lyr status --full`
3. Check logs with debug logging: `linkedin-lyr mcp --log-level DEBUG`

## Best Practices

1. **Session Management**: Re-import cookies periodically to maintain fresh sessions
2. **Browser Selection**: Use Brave for best bot-detection resistance
3. **Error Handling**: Always check session status before MCP operations
4. **Rate Limiting**: Avoid rapid successive requests to prevent LinkedIn rate limits
5. **Cookie Security**: Cookie files are stored with restrictive permissions (0600)

## Architecture

This MCP server uses **Obscura** as the browser backend, providing:

- 99.85% faster startup time (0.003s vs 2.0s)
- 99.6% less memory usage (0.61MB vs 150MB)
- 66.8% faster page fetches (0.829s vs 2.5s)
- 76.7% smaller binary size (70MB vs 300MB)

The system automatically manages the Obscura binary and handles version updates transparently.

## See Also

- [Project README](https://github.com/stickerdaniel/linkedin-mcp-server)
- [Obscura Documentation](https://github.com/johnusecase/obscura)
- [MCP Specification](https://modelcontextprotocol.io)
