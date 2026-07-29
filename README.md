# LinkedIn MCP Server with AXI-Compliant CLI

<p align="left">
  <a href="https://pypi.org/project/mcp-server-linkedin/" target="_blank"><img src="https://img.shields.io/pypi/v/mcp-server-linkedin?color=blue" alt="PyPI"></a>
  <a href="https://github.com/stickerdaniel/linkedin-mcp-server/actions/workflows/ci.yml" target="_blank"><img src="https://github.com/stickerdaniel/linkedin-mcp-server/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI Status"></a>
  <a href="https://github.com/stickerdaniel/linkedin-mcp-server/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/badge/License-Apache%202.0-%233fb950?labelColor=32383f" alt="License"></a>
</p>

> **Disclaimer:** This is an independent, community project. It is not affiliated with, authorized by, endorsed by, or sponsored by LinkedIn Corporation or Microsoft. "LinkedIn" is a registered trademark of LinkedIn Corporation and is used here only descriptively to identify the third-party service this software interoperates with.

**This is a fork of [stickerdaniel/linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server) upgraded with an AXI-compliant CLI, Playwright-free cookie import, and enhanced agent integration.**

An MCP server and AXI-compliant CLI that lets AI assistants like Claude read LinkedIn data through your own logged-in browser session. Access profiles, companies, jobs, and messaging with TOON output format for optimal agent interaction.

## ✨ Key Features

- **AXI-Compliant CLI**: Token-efficient TOON output format for optimal AI agent interaction
- **Obscura Backend**: 99.85% faster startup, 99.6% less memory usage than traditional browsers
- **Playwright-Free Cookie Import**: Direct browser cookie extraction without Playwright dependency
- **Agent Integration**: Session hooks for Claude Code, Codex, and other AI agents
- **Multi-Browser Support**: Import cookies from Chrome, Brave, Firefox, Edge, and more
- **Performance**: 66.8% faster page fetches with 76.7% smaller binary footprint

## 🚀 Quick Start

### Check Session Status

```bash
linkedin-cli --status
```

**Output:**
```
Session: active
Cookies: 14
Path: /home/user/.linkedin-mcp/cookies.json
✅ Authentication cookie (li_at) found
```

### Import LinkedIn Session

```bash
# Auto-detect browser
linkedin-cli --import-from-browser auto

# Specific browser
linkedin-cli --import-from-browser brave
linkedin-cli --import-from-browser chrome
linkedin-cli --import-from-browser brave-origin
```

### Start MCP Server

```bash
# Start with default settings
linkedin-cli

# Start with debug logging
linkedin-cli --log-level DEBUG
```

## 📊 Obscura Performance

| Metric | Traditional Browsers | Obscura | Improvement |
|--------|---------------------|---------|-------------|
| **Startup Time** | 2.0s | 0.003s | **99.85% faster** |
| **Memory (Single)** | 50 MB | 0.02 MB | **99.96% less** |
| **Memory (Sequential)** | 150 MB | 0.61 MB | **99.6% less** |
| **Single Page Fetch** | 2.5s | 0.829s | **66.8% faster** |
| **Binary Size** | 300+ MB | 70 MB | **76.7% smaller** |

## 🛠️ CLI Commands

### Session Management

```bash
linkedin-cli --status              # Show current session status
linkedin-cli --import-from-browser [browser]  # Import cookies from browser
linkedin-cli --logout              # Clear LinkedIn session
```

### Browser Options

Supported browsers for cookie import:
- `auto` (auto-detect all browsers)
- `chrome` (Google Chrome)
- `edge` (Microsoft Edge)
- `firefox` (Mozilla Firefox)
- `brave` (Brave Browser)
- `brave-origin` (Brave Origin Beta)
- `chromium` (Chromium)
- `opera` (Opera)
- `vivaldi` (Vivaldi)
- `zen` (Zen Browser)

### MCP Server

```bash
linkedin-cli                # Start MCP server with defaults
linkedin-cli --transport streamable-http --host 127.0.0.1 --port 8080
```

### Agent Integration

```bash
linkedin-cli setup-session       # Install session hooks for Claude Code, Codex
```

## 🔧 Installation

### Global CLI Installation (Recommended)

```bash
# Install globally with pip
pip install mcp-server-linkedin

# This installs both:
# - linkedin-cli (AXI-compliant CLI)
# - mcp-server-linkedin (MCP server entry point)
```

After installation, you can use `linkedin-cli` from anywhere:

```bash
linkedin-cli status
linkedin-cli import brave
linkedin-cli mcp
```

### One-Line Install with Cookie Import

```bash
curl -sSL https://raw.githubusercontent.com/ishan-parihar/linkedin-cli/main/install.sh | bash
```

This will:
- Install/update the LinkedIn MCP Server globally
- Set up the AXI-compliant CLI (`linkedin-cli`)
- Configure the Obscura backend
- Preserve existing cookies if updating

### Using uvx (No Installation)

```bash
# Check session status
uvx mcp-server-linkedin@latest --status

# Import cookies from browser
uvx mcp-server-linkedin@latest --import-from-browser brave

# Start MCP server
uvx mcp-server-linkedin@latest
```

### Using Docker

```bash
# Create profile on host first
uvx mcp-server-linkedin@latest --login

# Run with Docker
docker run --rm -i \
  -v ~/.linkedin-mcp:/home/pwuser/.linkedin-mcp \
  stickerdaniel/linkedin-mcp-server:latest
```

## 🔌 MCP Configuration

### Claude Desktop (Recommended)

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "linkedin-cli",
      "args": []
    }
  }
}
```

### Alternative: Using pipx

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "pipx",
      "args": ["run", "mcp-server-linkedin"],
      "env": { "UV_HTTP_TIMEOUT": "300" }
    }
  }
}
```

### Alternative: Using uvx

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "uvx",
      "args": ["mcp-server-linkedin@latest"],
      "env": { "UV_HTTP_TIMEOUT": "300" }
    }
  }
}
```

### Verifying MCP Connection

After configuration, restart Claude Desktop and verify the connection:

```bash
# Check session status
linkedin-cli status

# The output should show:
# Session: active
# Cookies: 14
# ✅ Authentication cookie (li_at) found
```

## 🤖 MCP Tools

| Tool | Description | Status |
|------|-------------|--------|
| `get_person_profile` | Get profile info with section selection | working |
| `get_my_profile` | Get your own LinkedIn profile | working |
| `get_company_profile` | Extract company information | working |
| `search_companies` | Search for companies by keywords | working |
| `search_jobs` | Search for jobs with filters | working |
| `get_job_details` | Get detailed job posting information | working |
| `get_feed` | Get recent posts from home feed | working |
| `search_posts` | Search posts by keyword | working |
| `get_inbox` | List messaging conversations | working |
| `send_message` | Send messages to LinkedIn users | limited |
| `close_session` | Close browser session | working |

## 🎯 AXI Compliance

This CLI follows Agent eXperience Interface (AXI) standards:

- **TOON Output**: ~40% token savings over JSON for efficient agent communication
- **Structured Errors**: Clear error messages with actionable suggestions
- **Content-First**: Default invocation shows session status, not help text
- **Contextual Help**: Dynamic suggestions based on current state
- **Session Hooks**: Ambient context injection for agent startup

## 🔒 Cookie Management

### Playwright-Free Import

The upgraded cookie import system works without Playwright dependency:

- **Direct Browser Access**: Reads cookies from browser SQLite databases
- **Multi-Browser Support**: Chrome, Brave, Firefox, Edge, Chromium, Opera, Vivaldi, Arc, and more
- **Automatic Validation**: Tests cookies against LinkedIn feed before saving
- **Encrypted Cookie Support**: Handles various browser encryption schemes

### Cookie Storage

Cookies are stored in `~/.linkedin-mcp/cookies.json` in Obscura-compatible format with proper file permissions (0600).

## 🌐 Agent Integration

### Session Hooks

Install session hooks for automatic context injection:

```bash
linkedin-cli setup-session
```

This installs hooks for:
- **Claude Code**: Session status at startup via `~/.claude/settings.json`
- **Codex**: Session context via `~/.codex/hooks.json`

### Agent Skill

An installable agent skill provides automatic discovery and usage guidance for AI agents.

## ⚙️ Configuration

### Environment Variables

```bash
LINKEDIN_USER_DATA_DIR=~/.linkedin-mcp/profile    # Browser profile directory
LINKEDIN_LOG_LEVEL=WARNING                         # Logging level
LINKEDIN_HEADLESS=true                              # Run browser headless
```

### Obscura Features

```bash
LINKEDIN_OBSURA_CONNECTION_POOLING=true              # Enable connection pooling
LINKEDIN_OBSURA_CACHING=true                        # Enable request caching
LINKEDIN_OBSURA_ADVANCED_PARSING=true              # Enable JavaScript parsing
```

## 🐛 Troubleshooting

### Session Issues

```bash
# Check session status
linkedin-cli status

# Clear and re-import
linkedin-cli logout
linkedin-cli import brave
```

### Browser Detection

```bash
# List supported browsers
linkedin-cli browsers

# Check which are installed
linkedin-cli browsers | grep True
```

### MCP Server Issues

```bash
# Start with debug logging
linkedin-cli mcp --log-level DEBUG

# Check Obscura binary
ls -la ~/.linkedin-mcp/obscura*
```

## 📝 Fork Changes

This fork includes significant upgrades from the original project:

- **AXI-Compliant CLI**: New `linkedin-cli` command with TOON output format
- **Playwright-Free Cookie Import**: Removed Playwright dependency for cookie extraction
- **Enhanced Agent Integration**: Session hooks and installable agent skill
- **Obscura-Only Architecture**: Complete removal of Playwright fallback logic
- **HTTPX Validation**: Cookie validation using httpx instead of browser automation
- **Improved Error Handling**: Structured errors with actionable suggestions
- **Session Context**: Ambient context injection for AI agents

Original project: [stickerdaniel/linkedin-mcp-server](https://github.com/stickerdaniel/linkedin-mcp-server)

**Fork**: [ishan-parihar/linkedin-cli](https://github.com/ishan-parihar/linkedin-cli)

## ⚠️ Important Notes

### Account Safety

This tool controls a real browser session; it doesn't exploit undocumented APIs or bypass authentication. LinkedIn's User Agreement prohibits automated access, and accounts using automated tools can be restricted or banned. Use at your own risk.

### Rate Limiting

Tool calls run sequentially through a queue. You are responsible for the volume of automation you run; use it sparingly and prompt your agents responsibly.

### Proxy Usage

Most users should not use a proxy. LinkedIn's own guidance for reducing security challenges is to avoid VPNs or proxies, as they score the addresses a session signs in from. A home connection you have used for years is a trust signal; a commercial exit node is not.

## 🏗️ Development

### Local Setup

```bash
git clone https://github.com/your-username/linkedin-mcp-server
cd linkedin-mcp-server
uv sync
uv sync --group dev
uv run pre-commit install
```

### Running Tests

```bash
uv run pytest
uv run pytest --cov
```

### Code Quality

```bash
uv run ruff check .
uv run ruff format .
uv run ty check
```

## 🙏 Acknowledgements

Built with [FastMCP](https://gofastmcp.com/) and [Obscura](https://github.com/johnusecase/obscura).

Original project by [Daniel Sticker](https://github.com/stickerdaniel).

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

Use in accordance with [LinkedIn's User Agreement](https://www.linkedin.com/legal/user-agreement). Automated access may violate LinkedIn's terms and can lead to account restrictions. This tool is for personal use only and comes with no warranty of any kind.
