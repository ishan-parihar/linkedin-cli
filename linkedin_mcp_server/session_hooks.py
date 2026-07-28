"""
Session hooks for ambient context integration.

Provides Claude Code, Codex, and other agent integrations with live session
context at startup, following AXI standards for ambient context.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from linkedin_mcp_server.obscura_cookie_import import (
    ObscuraCookieManager,
    ObscuraSessionValidator,
)
from linkedin_mcp_server.session_state import auth_root_dir

logger = logging.getLogger(__name__)


class SessionHookManager:
    """Manage session hooks for agent integrations."""

    def __init__(self):
        self.auth_root = auth_root_dir()
        self.cookie_manager = ObscuraCookieManager(self.auth_root)
        self.validator = ObscuraSessionValidator(self.cookie_manager)

    def get_session_context(self) -> dict[str, Any]:
        """Get current session context for agents."""
        validation = self.validator.validate_session()
        
        context = {
            "bin": self._get_bin_path(),
            "description": "LinkedIn MCP Server - Manage LinkedIn authentication and scraping",
            "session": {
                "valid": validation["valid"],
                "reason": validation.get("reason"),
                "message": validation.get("message"),
            }
        }
        
        if validation["valid"]:
            cookies = self.cookie_manager.load_cookies()
            context["session"]["cookies"] = len(cookies)
            context["session"]["path"] = str(self.cookie_manager.cookie_path)
        
        return context

    def _get_bin_path(self) -> str:
        """Get the absolute path of the current executable."""
        if hasattr(sys, "frozen"):
            return sys.executable
        return Path(__file__).parent.absolute().as_posix()

    def output_toon_context(self) -> None:
        """Output session context in TOON format."""
        context = self.get_session_context()
        
        # Output in TOON format
        print(f"bin: {context['bin']}")
        print(f"description: {context['description']}")
        
        session = context["session"]
        if session["valid"]:
            print(f"session: valid ({session['cookies']} cookies)")
        else:
            print(f"session: {session['reason']}")
            print(f"message: {session['message']}")
        
        # Add help suggestions
        if not session["valid"]:
            print("\nhelp[2]:")
            print("  Run 'linkedin-cli import' to set up authentication")
            print("  Run 'linkedin-cli browsers' to list supported browsers")
        else:
            print("\nhelp[2]:")
            print("  Run 'linkedin-cli status' for session details")
            print("  Run 'linkedin-cli mcp' to start the MCP server")


def setup_claude_code_hook() -> bool:
    """Set up Claude Code session hook."""
    try:
        claude_config_dir = Path.home() / ".claude"
        claude_config_file = claude_config_dir / "settings.json"
        
        claude_config_dir.mkdir(exist_ok=True)
        
        # Read existing config
        config = {}
        if claude_config_file.exists():
            with open(claude_config_file) as f:
                config = json.load(f)
        
        # Add session start hook
        if "sessionStart" not in config:
            config["sessionStart"] = []
        
        # Ensure sessionStart is a list
        if not isinstance(config["sessionStart"], list):
            config["sessionStart"] = []
        
        hook_command = "linkedin-cli status"
        
        # Check if hook already exists
        if not any(hook_command in str(hook) for hook in config["sessionStart"]):
            config["sessionStart"].append({
                "command": hook_command,
                "description": "LinkedIn MCP Server session context"
            })
            
            with open(claude_config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info("Claude Code hook installed")
            return True
        
        return False
    except Exception as e:
        logger.error("Failed to install Claude Code hook: %s", e)
        return False


def setup_codex_hook() -> bool:
    """Set up Codex session hook."""
    try:
        codex_config_dir = Path.home() / ".codex"
        codex_config_file = codex_config_dir / "hooks.json"
        
        codex_config_dir.mkdir(exist_ok=True)
        
        # Read existing config
        config = {}
        if codex_config_file.exists():
            with open(codex_config_file) as f:
                config = json.load(f)
        
        # Ensure hooks feature is enabled
        if "features" not in config:
            config["features"] = {}
        config["features"]["hooks"] = True
        
        # Add session start hook
        if "SessionStart" not in config:
            config["SessionStart"] = []
        
        # Ensure SessionStart is a list
        if not isinstance(config["SessionStart"], list):
            config["SessionStart"] = []
        
        hook_command = "linkedin-cli status"
        
        # Check if hook already exists
        if not any(hook_command in str(hook) for hook in config["SessionStart"]):
            config["SessionStart"].append({
                "command": hook_command,
                "description": "LinkedIn MCP Server session context"
            })
            
            with open(codex_config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info("Codex hook installed")
            return True
        
        return False
    except Exception as e:
        logger.error("Failed to install Codex hook: %s", e)
        return False


def install_hooks(agent: str = "all") -> dict[str, bool]:
    """Install session hooks for specified agents."""
    results = {}
    
    if agent in ("all", "claude"):
        results["claude"] = setup_claude_code_hook()
    
    if agent in ("all", "codex"):
        results["codex"] = setup_codex_hook()
    
    return results


if __name__ == "__main__":
    # Test session context output
    manager = SessionHookManager()
    manager.output_toon_context()
