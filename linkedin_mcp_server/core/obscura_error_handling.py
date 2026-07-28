"""
Error handling and logging utilities for Obscura browser operations.

Provides comprehensive error handling, logging, and performance metrics
for Obscura-based browser operations.
"""

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class ObscuraError(Exception):
    """Base exception for Obscura-related errors."""
    pass


class ObscuraTimeoutError(ObscuraError):
    """Obscura operation timed out."""
    pass


class ObscuraFetchError(ObscuraError):
    """Obscura fetch operation failed."""
    pass


class ObscuraEvalError(ObscuraError):
    """Obscura JavaScript evaluation failed."""
    pass


class ObscuraCookieError(ObscuraError):
    """Obscura cookie operation failed."""
    pass


class ObscuraStartupError(ObscuraError):
    """Obscura browser startup failed."""
    pass


def handle_obscura_error(error: Exception, context: str) -> None:
    """Handle Obscura errors with appropriate logging."""
    if isinstance(error, subprocess.TimeoutExpired):
        logger.error(
            "Obscura timeout in %s: %s. Consider increasing timeout.",
            context, str(error)
        )
    elif isinstance(error, subprocess.CalledProcessError):
        logger.error(
            "Obscura process error in %s: returncode=%d, stderr=%s",
            context, error.returncode, error.stderr[:200] if error.stderr else "empty"
        )
    else:
        logger.error("Obscura error in %s: %s", context, str(error))


def log_obscura_operation(operation: str, details: dict[str, Any] | None = None) -> None:
    """Log Obscura operations with structured details."""
    if details:
        logger.info("Obscura operation: %s - %s", operation, details)
    else:
        logger.info("Obscura operation: %s", operation)


def log_obscura_performance(operation: str, duration_seconds: float, details: dict[str, Any] | None = None) -> None:
    """Log Obscura performance metrics."""
    perf_data = {
        "operation": operation,
        "duration_seconds": duration_seconds,
        **(details or {})
    }
    logger.info("Obscura performance: %s", perf_data)


def validate_obscura_binary() -> bool:
    """Validate that Obscura binary is available and executable."""
    import os
    from pathlib import Path
    
    obscura_path = Path("/tmp/obscura")
    if not obscura_path.exists():
        logger.error("Obscura binary not found at %s", obscura_path)
        return False
    
    if not os.access(obscura_path, os.X_OK):
        logger.error("Obscura binary is not executable: %s", obscura_path)
        return False
    
    # Try running obscura --help to validate it works
    try:
        result = subprocess.run(
            [str(obscura_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("Obscura binary validated successfully")
            return True
        else:
            logger.error("Obscura binary validation failed: returncode=%d", result.returncode)
            return False
    except Exception as e:
        logger.error("Obscura binary validation error: %s", e)
        return False


def check_obscura_health() -> dict[str, Any]:
    """Check Obscura health and return status information."""
    health_status = {
        "binary_available": False,
        "binary_executable": False,
        "basic_functionality": False,
        "version": None,
        "errors": []
    }
    
    # Check binary availability
    from pathlib import Path
    obscura_path = Path("/tmp/obscura")
    health_status["binary_available"] = obscura_path.exists()
    
    if not health_status["binary_available"]:
        health_status["errors"].append("Binary not found")
        return health_status
    
    # Check executable permissions
    import os
    health_status["binary_executable"] = os.access(obscura_path, os.X_OK)
    if not health_status["binary_executable"]:
        health_status["errors"].append("Binary not executable")
    
    # Check basic functionality
    try:
        result = subprocess.run(
            [str(obscura_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        health_status["basic_functionality"] = result.returncode == 0
        if not health_status["basic_functionality"]:
            health_status["errors"].append(f"Help command failed: returncode={result.returncode}")
    except subprocess.TimeoutExpired:
        health_status["errors"].append("Binary timeout during health check")
    except Exception as e:
        health_status["errors"].append(f"Health check error: {e}")
    
    return health_status


def log_backend_selection(backend: str, reason: str) -> None:
    """Log backend selection decision."""
    logger.info("Backend selection: %s (reason: %s)", backend, reason)


def log_fallback_attempt(original_backend: str, fallback_backend: str, reason: str) -> None:
    """Log fallback attempt from one backend to another."""
    logger.warning(
        "Backend fallback: %s -> %s (reason: %s)",
        original_backend, fallback_backend, reason
    )