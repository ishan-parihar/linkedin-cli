"""LinkedIn MCP Server main CLI application entry point."""

import asyncio
import json
import logging
import os
import sys
from typing import Literal

import inquirer

from linkedin_mcp_server.bootstrap import (
    configure_browser_environment,
    ensure_browser_installed,
)
from linkedin_mcp_server.core import AuthenticationError
from linkedin_mcp_server.authentication import clear_auth_state
from linkedin_mcp_server.config import get_config
from linkedin_mcp_server.drivers.browser import (
    close_browser,
    experimental_persist_derived_runtime,
    get_or_create_browser,
    get_profile_dir,
    profile_exists,
    set_headless,
)
from linkedin_mcp_server.debug_trace import should_keep_traces
from linkedin_mcp_server.logging_config import configure_logging, teardown_trace_logging
from linkedin_mcp_server.session_state import (
    get_runtime_id,
    load_runtime_state,
    load_source_state,
    portable_cookie_path,
    runtime_profile_dir,
    runtime_storage_state_path,
    source_state_path,
)
from linkedin_mcp_server.server import create_mcp_server
from linkedin_mcp_server.setup import run_profile_creation

logger = logging.getLogger(__name__)


def choose_transport_interactive() -> Literal["stdio", "streamable-http"]:
    """Prompt user for transport mode using inquirer."""
    questions = [
        inquirer.List(
            "transport",
            message="Choose mcp transport mode",
            choices=[
                ("stdio (Default CLI mode)", "stdio"),
                ("streamable-http (HTTP server mode)", "streamable-http"),
            ],
            default="stdio",
        )
    ]
    answers = inquirer.prompt(questions)

    if not answers:
        raise KeyboardInterrupt("Transport selection cancelled by user")

    return answers["transport"]


def clear_profile_and_exit() -> None:
    """Clear LinkedIn browser profile and exit."""
    config = get_config()

    configure_logging(
        log_level=config.server.log_level,
        json_format=not config.is_interactive and config.server.log_level != "DEBUG",
    )

    version = get_version()
    logger.info(f"LinkedIn MCP Server v{version} - Profile Clear mode")

    auth_root = get_profile_dir().parent

    if not (
        profile_exists(get_profile_dir())
        or portable_cookie_path(get_profile_dir()).exists()
        or source_state_path(get_profile_dir()).exists()
    ):
        print("ℹ️  No authentication state found")
        print("Nothing to clear.")
        sys.exit(0)

    print(f"🔑 Clear LinkedIn authentication state from {auth_root}?")

    try:
        confirmation = (
            input("Are you sure you want to clear the profile? (y/N): ").strip().lower()
        )
        if confirmation not in ("y", "yes"):
            print("❌ Operation cancelled")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(0)

    if clear_auth_state(get_profile_dir()):
        print("✅ LinkedIn authentication state cleared successfully!")
    else:
        print("❌ Failed to clear authentication state")
        sys.exit(1)

    sys.exit(0)


def get_profile_and_exit() -> None:
    """Create profile interactively and exit."""
    config = get_config()

    configure_logging(
        log_level=config.server.log_level,
        json_format=not config.is_interactive and config.server.log_level != "DEBUG",
    )

    version = get_version()
    logger.info(f"LinkedIn MCP Server v{version} - Session Creation mode")

    user_data_dir = config.browser.user_data_dir
    success = run_profile_creation(user_data_dir)

    sys.exit(0 if success else 1)


def import_from_browser_and_exit() -> None:
    """Import a LinkedIn session from a local browser, validate, persist, exit."""
    config = get_config()
    configure_logging(
        log_level=config.server.log_level,
        json_format=not config.is_interactive and config.server.log_level != "DEBUG",
    )
    logger.info("LinkedIn MCP Server v%s - Browser Import mode", get_version())

    # Use the new browser_cookie_extractor module
    from linkedin_mcp_server.browser_cookie_extractor import (
        extract_linkedin_cookies,
        format_cookies_for_linkedin_mcp,
    )
    from linkedin_mcp_server.session_state import auth_root_dir

    auth_root = auth_root_dir()
    output_path = auth_root / "cookies.json"
    
    # Get browser selector from config
    browser = (
        None
        if config.server.import_from_browser == "auto"
        else config.server.import_from_browser
    )

    if config.is_interactive:
        print(
            "ℹ️  Importing LinkedIn cookies from browser. "
            "On macOS, you may be prompted to allow keychain access."
        )

    try:
        # Extract cookies using browser_cookie3 (no browser environment setup needed)
        cookie_data = extract_linkedin_cookies(browser=browser)
        if not cookie_data:
            print(f"❌ No LinkedIn cookies found")
            if browser:
                print(f"   Tried browser: {browser}")
            else:
                print("   Tried auto-detection across all browsers")
            print("   Log into LinkedIn in your browser first, or run with --login.")
            sys.exit(1)

        # Format cookies for LinkedIn MCP
        formatted_cookies = format_cookies_for_linkedin_mcp(cookie_data)

        # Save cookies
        os.makedirs(auth_root, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(formatted_cookies, f, indent=2)

        # Set proper permissions
        os.chmod(output_path, 0o600)

        # Verify li_at cookie is present
        li_at_found = any(c.get("name") == "li_at" for c in formatted_cookies)
        
        print(f"✅ Successfully imported LinkedIn cookies")
        print(f"   Source: {cookie_data.get('source', 'unknown')}")
        print(f"   Cookies: {len(formatted_cookies)}")
        print(f"   Path: {output_path}")
        
        if li_at_found:
            print(f"   ✅ Authentication cookie (li_at) found")
        else:
            print(f"   ⚠️  Warning: Authentication cookie (li_at) not found")
            print(f"   The session may not be fully functional")
        
        print(f"   Run 'linkedin-cli --status' to verify your session")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Failed to import cookies: {e}")
        logger.exception("Cookie import failed")
        sys.exit(1)


def profile_info_and_exit() -> None:
    """Check profile validity and display info, then exit."""
    config = get_config()

    configure_logging(
        log_level=config.server.log_level,
        json_format=not config.is_interactive and config.server.log_level != "DEBUG",
    )

    version = get_version()
    logger.info(f"LinkedIn MCP Server v{version} - Session Info mode")

    from linkedin_mcp_server.session_state import auth_root_dir
    
    auth_root = auth_root_dir()
    cookies_path = auth_root / "cookies.json"
    
    # Simple cookie file check first
    if not cookies_path.exists():
        print(f"❌ No LinkedIn session found")
        print(f"   Run 'linkedin-cli --import-from-browser' to import cookies from your browser")
        print(f"   Or run 'linkedin-cli --login' to create a new session")
        sys.exit(0)
    
    # Check cookie file contents
    try:
        with open(cookies_path) as f:
            cookies = json.load(f)
        
        li_at_found = any(c.get("name") == "li_at" for c in cookies)
        
        print(f"Session: {'active' if li_at_found else 'invalid'}")
        print(f"Cookies: {len(cookies)}")
        print(f"Path: {cookies_path}")
        
        if li_at_found:
            print(f"✅ Authentication cookie (li_at) found")
        else:
            print(f"⚠️  Warning: Authentication cookie (li_at) not found")
            print(f"   Run 'linkedin-cli --import-from-browser' to refresh your session")
        
        sys.exit(0)
    except Exception as e:
        print(f"❌ Could not read session: {e}")
        sys.exit(1)


def get_version() -> str:
    """Get version from installed metadata with a source fallback."""
    try:
        from importlib.metadata import PackageNotFoundError, version

        for package_name in (
            "mcp-server-linkedin",
            "linkedin-scraper-mcp",
            "linkedin-mcp-server",
        ):
            try:
                return version(package_name)
            except PackageNotFoundError:
                continue
    except Exception:
        pass

    try:
        import os
        import tomllib

        pyproject_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "pyproject.toml"
        )
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "unknown"


def main() -> None:
    """Main application entry point."""
    config = get_config()

    # Configure logging
    configure_logging(
        log_level=config.server.log_level,
        json_format=not config.is_interactive and config.server.log_level != "DEBUG",
    )

    version = get_version()

    # Print banner in interactive mode
    if config.is_interactive:
        print(f"🔗 LinkedIn MCP Server v{version} 🔗")
        print("=" * 40)

    logger.info(f"LinkedIn MCP Server v{version}")

    try:
        # Configure browser environment only for modes that need it
        # --import-from-browser and --status don't need it (they use browser_cookie3)
        # --login and normal server startup do need it
        if config.server.login or not (config.server.import_from_browser or config.server.status):
            configure_browser_environment()

        # Set headless mode from config
        set_headless(config.browser.headless)

        # Handle --logout flag
        if config.server.logout:
            clear_profile_and_exit()

        # Ensure browser is installed for CLI modes that launch it.
        # Normal server startup uses async background setup instead. --login is
        # headed and needs full chromium; --status and --import-from-browser don't
        # need browser anymore (they use browser_cookie3 directly).
        if config.server.login:
            ensure_browser_installed(full=config.server.login)

        # Handle --import-from-browser flag
        if config.server.import_from_browser:
            import_from_browser_and_exit()

        # Handle --login flag
        if config.server.login:
            get_profile_and_exit()

        # Handle --status flag
        if config.server.status:
            profile_info_and_exit()

        logger.debug(f"Server configuration: {config}")

        # Phase 1: Server Runtime
        try:
            transport = config.server.transport

            # Prompt for transport in interactive mode if not explicitly set
            if config.is_interactive and not config.server.transport_explicitly_set:
                print("\n🚀 Server ready! Choose transport mode:")
                transport = choose_transport_interactive()
                # Record the answer rather than keeping it in a local. Two
                # checks read the stored transport to decide how exposed this
                # process is: the bind-address warning, and the gate that
                # decides whether reading the local browser's LinkedIn cookie
                # is safe. Leaving it at stdio told them a listening HTTP
                # server was a private one. Re-validating applies the HTTP
                # rules that were skipped when the value said stdio.
                config.server.transport = transport
                config.validate()

            # Create and run the MCP server
            mcp = create_mcp_server(tool_timeout=config.server.tool_timeout_seconds)

            if transport == "streamable-http":
                # Validate Host and Origin. Without this a website the user
                # merely visits can point a hostname at this server's address
                # and have the user's own browser drive tools with the
                # logged-in LinkedIn session. The request comes from inside, so
                # a firewall does not help. The MCP specification requires this
                # for local HTTP servers, and it is off unless asked for.
                #
                # Both checks are needed, and the Host one carries most of the
                # weight. A rebinding attack sends its own domain as *both*
                # Host and Origin, so those agree and origin validation alone
                # lets it through; what gives it away is that the Host is not a
                # name this server answers to. Requests carrying no Origin at
                # all stay allowed, which is every non-browser client.
                #
                # True rather than "auto": "auto" only validates when the
                # accepted connection landed on a loopback address, so a server
                # bound to 0.0.0.0 and reached over its LAN address checked
                # nothing at all, which is the exposed case where it matters
                # most. Measured before this: an attacker Host and Origin over
                # the LAN address were served, while the same request to
                # 127.0.0.1 was refused.
                #
                # Strict accepts localhost and the address the connection
                # arrived on, which covers the documented flows. It does not
                # accept a DNS name such as a machine name or a public name in
                # front of a proxy, so those need the proxy to rewrite the
                # upstream Host, or the name listed explicitly. The README says
                # so next to the exposed-bind example, because a 421 nobody can
                # explain is how a guard like this ends up switched off.
                #
                # Deliberately no host wildcard: it would accept any Host and
                # reopen the same hole from the other side.
                mcp.run(
                    transport=transport,
                    host=config.server.host,
                    port=config.server.port,
                    path=config.server.path,
                    host_origin_protection=True,
                )
            else:
                mcp.run(transport=transport)

        except KeyboardInterrupt:
            exit_gracefully(0)

        except Exception as e:
            logger.exception(f"Server runtime error: {e}")
            if config.is_interactive:
                print(f"\n❌ Server error: {e}")
            exit_gracefully(1)
    finally:
        teardown_trace_logging(keep_traces=should_keep_traces())


def exit_gracefully(exit_code: int = 0) -> None:
    """Exit the application gracefully with browser cleanup."""
    try:
        asyncio.run(close_browser())
    except Exception:
        pass  # Best effort cleanup
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit_gracefully(0)
    except Exception as e:
        logger.exception(
            f"Error running MCP server: {e}",
            extra={"exception_type": type(e).__name__, "exception_message": str(e)},
        )
        exit_gracefully(1)
