#!/usr/bin/env python3
"""
LinkedIn CLI full entry point - AXI-compliant interface with full functionality.

This script provides the AXI-compliant CLI interface for LinkedIn MCP Server.
Run with commands like: linkedin-cli status, linkedin-cli import, etc.

This version includes full cookie import functionality using browser_cookie3.
"""

import sys
import json
import logging
import os
from pathlib import Path

# Set up basic logging BEFORE any other imports
logging.basicConfig(level=logging.ERROR)

# AXI CLI commands
axi_commands = {"status", "browsers", "import", "logout", "mcp", "help"}

def toon_output(data: dict) -> None:
    """Output data in TOON format to stdout."""
    for key, value in data.items():
        if isinstance(value, list) and value:
            if isinstance(value[0], dict):
                schema = ",".join(value[0].keys())
                print(f"{key}[{len(value)}]{{{schema}}}:")
                for item in value:
                    row = ",".join(str(v) for v in item.values())
                    print(f"  {row}")
            else:
                print(f"{key}[{len(value)}]:")
                for item in value:
                    print(f"  {item}")
        elif isinstance(value, dict):
            print(f"{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")

def toon_error(message: str, help_text: str = None) -> None:
    """Output structured error in TOON format."""
    print(f"error: {message}")
    if help_text:
        print(f"help: {help_text}")

def toon_help(help_items: list) -> None:
    """Output help suggestions in TOON format."""
    print(f"help[{len(help_items)}]:")
    for item in help_items:
        print(f"  {item}")

def cmd_status(full: bool = False) -> None:
    """Show current LinkedIn session status."""
    from linkedin_mcp_server.session_state import auth_root_dir
    
    auth_root = auth_root_dir()
    cookie_path = auth_root / "cookies.json"
    
    if not cookie_path.exists():
        toon_output({
            "bin": sys.argv[0],
            "description": "Manage LinkedIn authentication and MCP server configuration",
            "session": "none",
            "message": "No LinkedIn session found. Run 'linkedin-cli import' to set up authentication.",
        })
        toon_help([
            "Run 'linkedin-cli import' to import cookies from your browser",
            "Run 'linkedin-cli browsers' to list supported browsers",
        ])
        return
    
    try:
        with open(cookie_path) as f:
            cookies = json.load(f)
        li_at_found = any(c.get("name") == "li_at" for c in cookies)
        
        result = {
            "bin": sys.argv[0],
            "description": "Manage LinkedIn authentication and MCP server configuration",
            "session": "active" if li_at_found else "invalid",
            "cookies": len(cookies),
            "path": str(cookie_path),
        }
        
        if full:
            cookie_names = [c.get("name") for c in cookies]
            result["cookie_names"] = cookie_names
        
        toon_output(result)
        
        if not li_at_found:
            toon_help([
                "Run 'linkedin-cli import' to refresh your session",
                "Run 'linkedin-cli logout' to clear the invalid session",
            ])
    except Exception as e:
        toon_output({
            "bin": sys.argv[0],
            "description": "Manage LinkedIn authentication and MCP server configuration",
            "session": "error",
            "message": f"Could not read session: {e}",
        })

def cmd_browsers() -> None:
    """List supported browsers."""
    # Supported browsers by browser_cookie3
    browsers = [
        {"id": "chrome", "name": "Google Chrome", "engine": "chromium", "installed": True, "description": "Most widely used"},
        {"id": "edge", "name": "Microsoft Edge", "engine": "chromium", "installed": True, "description": "Built into Windows, Chromium-based"},
        {"id": "firefox", "name": "Mozilla Firefox", "engine": "firefox", "installed": True, "description": "Open-source, non-Chromium"},
        {"id": "brave", "name": "Brave", "engine": "chromium", "installed": True, "description": "Recommended — best bot-detection resistance"},
        {"id": "chromium", "name": "Chromium", "engine": "chromium", "installed": True, "description": "Open-source Chromium"},
        {"id": "opera", "name": "Opera", "engine": "chromium", "installed": True, "description": "Feature-rich Chromium browser"},
        {"id": "vivaldi", "name": "Vivaldi", "engine": "chromium", "installed": True, "description": "Customizable Chromium browser"},
    ]
    
    toon_output({
        "browsers": browsers,
        "count": f"{len(browsers)} supported",
    })
    
    toon_help([
        "Run 'linkedin-cli import' to auto-detect and import from available browsers",
        "browser_cookie3 will check all supported browsers automatically",
    ])

def cmd_import(browser: str = None) -> None:
    """Import LinkedIn cookies from browser using browser_cookie3."""
    from linkedin_mcp_server.browser_cookie_extractor import (
        extract_linkedin_cookies,
        format_cookies_for_linkedin_mcp,
    )
    from linkedin_mcp_server.session_state import auth_root_dir
    
    auth_root = auth_root_dir()
    output_path = auth_root / "cookies.json"
    
    # Extract cookies using browser_cookie3 (auto-detects available browsers)
    cookie_data = extract_linkedin_cookies()
    if not cookie_data:
        toon_error(
            "no LinkedIn cookies found in any browser",
            "log into LinkedIn in your browser first"
        )
        sys.exit(1)
    
    # Format cookies for LinkedIn MCP
    formatted_cookies = format_cookies_for_linkedin_mcp(cookie_data)
    
    # Save cookies
    os.makedirs(auth_root, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(formatted_cookies, f, indent=2)
    
    # Set proper permissions
    os.chmod(output_path, 0o600)
    
    toon_output({
        "status": "success",
        "browser": cookie_data.get("source", "unknown"),
        "cookies": len(formatted_cookies),
        "path": str(output_path),
    })
    
    toon_help([
        "Run 'linkedin-cli status' to verify your session",
        "Run 'linkedin-cli mcp' to start the MCP server",
    ])

def cmd_logout() -> None:
    """Clear LinkedIn session."""
    from linkedin_mcp_server.session_state import auth_root_dir
    
    auth_root = auth_root_dir()
    cookie_path = auth_root / "cookies.json"
    
    if not cookie_path.exists():
        toon_output({
            "status": "no-op",
            "message": "No session to clear",
        })
        return
    
    try:
        cookie_path.unlink()
        toon_output({
            "status": "success",
            "message": "LinkedIn session cleared",
        })
    except Exception as e:
        toon_error(
            f"failed to clear session: {e}",
            "check file permissions"
        )
        sys.exit(1)

def cmd_mcp(args: list) -> None:
    """Start the MCP server."""
    # Import here to avoid argparse conflicts
    from linkedin_mcp_server.cli_main import main as mcp_main
    
    # Replace sys.argv to pass through to main()
    sys.argv = ["linkedin-mcp"] + args
    mcp_main()

def main() -> None:
    """Main entry point for AXI CLI."""
    if len(sys.argv) < 2:
        # No command provided, show status by default
        cmd_status()
        return
    
    command = sys.argv[1].lower()
    
    if command not in axi_commands:
        toon_error(
            f"unknown command '{command}'",
            "available commands: status, browsers, import, logout, mcp, help"
        )
        sys.exit(1)
    
    if command == "status":
        full = "--full" in sys.argv
        cmd_status(full)
    elif command == "browsers":
        cmd_browsers()
    elif command == "import":
        browser = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_import(browser)
    elif command == "logout":
        cmd_logout()
    elif command == "mcp":
        cmd_mcp(sys.argv[2:])
    elif command == "help":
        toon_output({
            "bin": sys.argv[0],
            "description": "Manage LinkedIn authentication and MCP server configuration",
        })
        toon_output({
            "commands": [
                "status               Show current LinkedIn session status",
                "browsers             List supported browsers",
                "import               Import LinkedIn cookies from browser (auto-detects)",
                "logout               Clear LinkedIn session",
                "mcp [args...]        Start the MCP server",
            ]
        })
        toon_output({
            "flags": [
                "--full               Show full details (for status command)",
                "--help               Show this help message",
            ]
        })

if __name__ == "__main__":
    main()