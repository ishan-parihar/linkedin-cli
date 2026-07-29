# MCP Configuration Guide

This guide explains how to wire up the LinkedIn MCP server with various AI agents and platforms.

## Claude Desktop (Recommended)

### Installation Steps

1. **Install linkedin-cli globally:**
   ```bash
   pip install mcp-server-linkedin
   # OR
   pipx install mcp-server-linkedin
   ```

2. **Configure Claude Desktop:**
   
   Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. **Add the MCP server configuration:**
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

4. **Restart Claude Desktop** to activate the server.

5. **Import LinkedIn cookies:**
   ```bash
   linkedin-cli --import-from-browser brave
   ```

6. **Verify session status:**
   ```bash
   linkedin-cli --status
   ```

### Alternative Configurations

#### Using pipx
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

#### Using uvx (No Installation)
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

#### Using Direct Path
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "/home/user/.local/bin/linkedin-cli",
      "args": []
    }
  }
}
```

## Other MCP Clients

### Cline (VS Code Extension)

Add to your Cline settings:
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

### Continue.dev

Configure in your MCP settings:
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

### Generic MCP Client

For any MCP-compatible client, use the standard configuration:
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

## Troubleshooting

### PATH Issues

If you get "command not found" errors:

1. **Check your PATH:**
   ```bash
   which linkedin-cli
   ```

2. **Ensure pipx is in PATH:**
   ```bash
   pipx ensurepath
   ```

3. **Use full path in configuration:**
   ```json
   {
     "mcpServers": {
       "linkedin": {
         "command": "/home/user/.local/bin/linkedin-cli",
         "args": []
       }
     }
   }
   ```

### Session Issues

If the MCP server can't find cookies:

1. **Check session status:**
   ```bash
   linkedin-cli --status
   ```

2. **Re-import cookies:**
   ```bash
   linkedin-cli --import-from-browser auto
   ```

3. **Check cookie file location:**
   ```bash
   ls -la ~/.linkedin-mcp/cookies.json
   ```

### Permission Issues

If you get permission errors:

1. **Check file permissions:**
   ```bash
   ls -la ~/.linkedin-mcp/cookies.json
   ```

2. **Fix permissions:**
   ```bash
   chmod 600 ~/.linkedin-mcp/cookies.json
   ```

## Environment Variables

You can configure the MCP server using environment variables:

```bash
# Browser profile directory
LINKEDIN_USER_DATA_DIR=~/.linkedin-mcp/profile

# Logging level
LINKEDIN_LOG_LEVEL=WARNING

# Headless mode
LINKEDIN_HEADLESS=true

# Obscura features
LINKEDIN_OBSURA_CONNECTION_POOLING=true
LINKEDIN_OBSURA_CACHING=true
LINKEDIN_OBSURA_ADVANCED_PARSING=true
```

Add these to your MCP configuration:
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "linkedin-cli",
      "args": [],
      "env": {
        "LINKEDIN_LOG_LEVEL": "DEBUG",
        "LINKEDIN_HEADLESS": "true"
      }
    }
  }
}
```

## Verification

After configuration, verify the MCP connection:

1. **Check CLI functionality:**
   ```bash
   linkedin-cli --status
   ```

2. **Test MCP server startup:**
   ```bash
   linkedin-cli
   ```

3. **Verify in Claude Desktop:**
   - Open Claude Desktop
   - Check the MCP tools are available
   - Try using a LinkedIn tool

## Advanced Configuration

### Custom Server Transport

For HTTP transport instead of stdio:
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "linkedin-cli",
      "args": ["--transport", "streamable-http", "--host", "127.0.0.1", "--port", "8080"]
    }
  }
}
```

### Debug Mode

Enable debug logging for troubleshooting:
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "linkedin-cli",
      "args": ["--log-level", "DEBUG"]
    }
  }
}
```

## Cookie Import Options

The MCP server supports multiple browsers for cookie import:

```bash
# Auto-detect
linkedin-cli --import-from-browser auto

# Specific browsers
linkedin-cli --import-from-browser chrome
linkedin-cli --import-from-browser brave
linkedin-cli --import-from-browser brave-origin
linkedin-cli --import-from-browser edge
linkedin-cli --import-from-browser firefox
linkedin-cli --import-from-browser chromium
linkedin-cli --import-from-browser opera
linkedin-cli --import-from-browser vivaldi
linkedin-cli --import-from-browser zen
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/ishan-parihar/linkedin-cli/issues
- Documentation: https://github.com/ishan-parihar/linkedin-cli#readme