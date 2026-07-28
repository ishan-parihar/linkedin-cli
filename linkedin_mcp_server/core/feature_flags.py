"""
Feature flags for Obscura backend configuration.

Provides configuration-based feature flags for Obscura backend features.
Playwright has been completely removed.
"""

import os
import logging
from typing import Literal

logger = logging.getLogger(__name__)

# Feature flag definitions
FEATURE_FLAGS = {
    "obscura_enabled": {
        "description": "Enable Obscura backend for LinkedIn scraping",
        "default": True,  # Always enabled
        "env_var": "LINKEDIN_OBSURA_ENABLED",
        "rollout_percentage": 100,  # 100% rollout
    },
    "obscura_force_mode": {
        "description": "Force Obscura backend (default and only option)",
        "default": True,  # Always forced
        "env_var": "LINKEDIN_OBSURA_FORCE",
        "rollout_percentage": 100,
    },
    "obscura_connection_pooling": {
        "description": "Enable connection pooling for Obscura instances",
        "default": False,
        "env_var": "LINKEDIN_OBSURA_CONNECTION_POOLING",
        "rollout_percentage": 0,
    },
    "obscura_caching": {
        "description": "Enable response caching for Obscura requests",
        "default": False,
        "env_var": "LINKEDIN_OBSURA_CACHING",
        "rollout_percentage": 0,
    },
    "obscura_advanced_parsing": {
        "description": "Enable advanced JavaScript-based content parsing",
        "default": False,
        "env_var": "LINKEDIN_OBSURA_ADVANCED_PARSING",
        "rollout_percentage": 0,
    },
}


def get_feature_flag(flag_name: str) -> bool:
    """Get the value of a feature flag.
    
    Priority:
    1. Environment variable
    2. Configuration file (if available)
    3. Default value
    """
    if flag_name not in FEATURE_FLAGS:
        logger.warning("Unknown feature flag: %s", flag_name)
        return False
    
    flag_config = FEATURE_FLAGS[flag_name]
    env_var = flag_config["env_var"]
    
    # Check environment variable
    env_value = os.getenv(env_var, "").strip().lower()
    if env_value in ("1", "true", "yes", "on"):
        logger.info("Feature flag %s enabled via environment variable %s", flag_name, env_var)
        return True
    elif env_value in ("0", "false", "no", "off"):
        logger.info("Feature flag %s disabled via environment variable %s", flag_name, env_var)
        return False
    
    # Check rollout percentage (for future use)
    # This would enable percentage-based rollouts
    rollout_percentage = flag_config.get("rollout_percentage", 0)
    if rollout_percentage > 0:
        # Simple hash-based rollout for consistent user experience
        import hashlib
        user_id = os.getenv("USER", "default")
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        if (hash_value % 100) < rollout_percentage:
            logger.info("Feature flag %s enabled via rollout (%d%%)", flag_name, rollout_percentage)
            return True
    
    # Use default value
    default_value = flag_config["default"]
    logger.debug("Feature flag %s using default value: %s", flag_name, default_value)
    return default_value


def set_feature_flag(flag_name: str, value: bool) -> None:
    """Set a feature flag value programmatically.
    
    This is primarily for testing and debugging. In production,
    feature flags should be controlled via environment variables.
    """
    if flag_name not in FEATURE_FLAGS:
        logger.warning("Cannot set unknown feature flag: %s", flag_name)
        return
    
    FEATURE_FLAGS[flag_name]["default"] = value
    logger.info("Feature flag %s set to %s programmatically", flag_name, value)


def get_all_feature_flags() -> dict[str, bool]:
    """Get all feature flag values."""
    return {
        flag_name: get_feature_flag(flag_name)
        for flag_name in FEATURE_FLAGS.keys()
    }


def is_obscura_enabled() -> bool:
    """Check if Obscura is enabled via feature flags (always True)."""
    return True


def is_obscura_advanced_feature_enabled(feature: str) -> bool:
    """Check if a specific Obscura advanced feature is enabled."""
    feature_flag = f"obscura_{feature}"
    return get_feature_flag(feature_flag)


def log_feature_flag_status() -> None:
    """Log the current status of all feature flags."""
    logger.info("Feature Flag Status:")
    for flag_name, value in get_all_feature_flags().items():
        flag_config = FEATURE_FLAGS[flag_name]
        status = "✓ ENABLED" if value else "✗ DISABLED"
        logger.info("  %s: %s - %s", flag_name, status, flag_config["description"])


class FeatureFlagContext:
    """Context manager for temporarily overriding feature flags."""
    
    def __init__(self, **overrides: bool):
        self.overrides = overrides
        self.original_values = {}
    
    def __enter__(self) -> "FeatureFlagContext":
        # Store original values
        for flag_name, value in self.overrides.items():
            if flag_name in FEATURE_FLAGS:
                self.original_values[flag_name] = FEATURE_FLAGS[flag_name]["default"]
                FEATURE_FLAGS[flag_name]["default"] = value
                logger.info("Temporarily set feature flag %s to %s", flag_name, value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Restore original values
        for flag_name, original_value in self.original_values.items():
            FEATURE_FLAGS[flag_name]["default"] = original_value
            logger.info("Restored feature flag %s to %s", flag_name, original_value)