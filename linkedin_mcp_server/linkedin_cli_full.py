#!/usr/bin/env python3
"""
LinkedIn CLI full entry point - AXI-compliant interface with full functionality.

This script provides the AXI-compliant CLI interface for LinkedIn MCP Server.
Run with commands like: linkedin-cli status, linkedin-cli import, etc.

This version includes full cookie import functionality without argparse conflicts.
"""

import sys
import json
import logging
from pathlib import Path

# Set up basic logging BEFORE any other imports
logging.basicConfig(level=logging.ERROR)

# AXI CLI commands
axi_commands = {"status", "browsers", "import", "logout", "mcp", "setup-session", "help"}

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
    auth_root = Path.home() / ".linkedin-mcp"
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
    # Import here to avoid argparse conflicts
    from linkedin_mcp_server.cookie_import import (
        detect_installed_browsers,
        BROWSER_REGISTRY,
    )
    
    installed = detect_installed_browsers()
    
    all_browsers = []
    for browser_id, profile in BROWSER_REGISTRY.items():
        is_installed = any(b_id == browser_id for b_id, _ in installed)
        all_browsers.append({
            "id": browser_id,
            "name": profile.name,
            "engine": profile.engine,
            "installed": is_installed,
            "description": profile.description,
        })
    
    toon_output({
        "browsers": all_browsers,
        "count": f"{len(installed)} of {len(all_browsers)} installed",
    })
    
    if not installed:
        toon_help([
            "Install a supported browser to import LinkedIn cookies",
            "Supported browsers: Brave, Chrome, Firefox, Edge, and more",
        ])

def cmd_import(browser: str = None) -> None:
    """Import LinkedIn cookies from browser."""
    # Import here to avoid argparse conflicts
    from linkedin_mcp_server.cookie_import import (
        extract_cookies_from_browser,
        auto_extract_cookies,
        import_cookies_for_linkedin,
        BROWSER_REGISTRY,
    )
    
    if browser and browser not in BROWSER_REGISTRY:
        valid_browsers = ", ".join(sorted(BROWSER_REGISTRY.keys()))
        toon_error(
            f"unknown browser '{browser}'",
            f"valid browsers: {valid_browsers}"
        )
        sys.exit(2)
    
    # Auto-detect if no browser specified
    if not browser:
        from linkedin_mcp_server.cookie_import import detect_installed_browsers
        installed = detect_installed_browsers()
        if not installed:
            toon_error(
                "no supported browsers found",
                "install a supported browser first (chrome, brave, firefox, edge, etc.)"
            )
            sys.exit(1)
        browser = installed[0][0]  # Use first available
    
    # Extract cookies
    cookies = extract_cookies_from_browser(browser)
    if not cookies:
        toon_error(
            f"no LinkedIn cookies found in {browser}",
            "log into LinkedIn in your browser first"
        )
        sys.exit(1)
    
    # Save cookies
    output_path = import_cookies_for_linkedin(browser)
    if not output_path:
        toon_error(
            "failed to save cookies",
            "check file permissions and disk space"
        )
        sys.exit(1)
    
    toon_output({
        "status": "success",
        "browser": browser,
        "cookies": len(cookies),
        "path": str(output_path),
        "cookie_names": list(cookies.keys()),
    })
    
    toon_help([
        "Run 'linkedin-cli status' to verify the session",
        "Run 'linkedin-cli mcp' to start the MCP server",
    ])

def cmd_logout() -> None:
    """Clear LinkedIn session."""
    auth_root = Path.home() / ".linkedin-mcp"
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

def cmd_setup_session() -> None:
    """Set up session hooks."""
    # Import here to avoid argparse conflicts
    from linkedin_mcp_server.session_hooks import (
        install_hooks,
    )
    
    results = install_hooks("all")
    
    toon_output({
        "hooks": results,
        "message": "Session hooks installed" if all(results.values()) else "Some hooks failed to install",
    })

def print_help() -> None:
    """Print comprehensive help information."""
    print("bin:", sys.argv[0])
    print("description: Manage LinkedIn authentication and MCP server configuration")
    print("\ncommands:")
    commands = [
        {"name": "status", "description": "Show current LinkedIn session status"},
        {"name": "browsers", "description": "List supported and installed browsers"},
        {"name": "import [browser]", "description": "Import LinkedIn cookies from browser"},
        {"name": "logout", "description": "Clear LinkedIn session"},
        {"name": "mcp [args...]", "description": "Start the MCP server"},
        {"name": "setup-session", "description": "Set up session hooks for agent integration"},
    ]
    
    for cmd in commands:
        print(f"  {cmd['name']:<20} {cmd['description']}")
    
    print("\nflags:")
    print("  --full               Show full details (for status command)")
    print("  --help               Show this help message")

def main():
    """Main entry point for AXI CLI."""
    # If no arguments or help request, show AXI help
    if not sys.argv[1:] or sys.argv[1] in ("--help", "-h", "help"):
        print_help()
        return 0
    
    command = sys.argv[1]
    command_args = sys.argv[2:]
    
    # If first argument is an AXI command, use AXI CLI
    if command in axi_commands:
        if command == "status":
            full = "--full" in command_args
            cmd_status(full=full)
        elif command == "browsers":
            cmd_browsers()
        elif command == "import":
            browser = command_args[0] if command_args and not command_args[0].startswith("--") else None
            cmd_import(browser=browser)
        elif command == "logout":
            cmd_logout()
        elif command == "mcp":
            cmd_mcp(command_args)
        elif command == "setup-session":
            cmd_setup_session()
        return 0
    
    # Otherwise show error and help
    print(f"error: unknown command '{command}'")
    print(f"help: valid commands: {', '.join(sorted(axi_commands))}")
    return 2

if __name__ == "__main__":
    sys.exit(main())
