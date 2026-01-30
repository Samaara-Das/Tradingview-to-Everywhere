"""
Configuration Management for TTE Tiered Orchestrator

Loads configuration from environment variables with sensible defaults.
Validates required settings on startup.

Usage:
    from config import config

    api_url = config.STOCK_BUDDY_API_URL
    config.validate()  # Raises ValueError if required settings missing
"""

import os
import logging
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Application configuration from environment variables."""

    # ===========================================
    # Stock Buddy API
    # ===========================================

    STOCK_BUDDY_API_URL = os.getenv(
        'STOCK_BUDDY_API_URL',
        'http://localhost:3000/api'
    )

    # ===========================================
    # Chrome Configuration
    # ===========================================

    # Support both CHROME_PROFILE_PATH and CHROME_PROFILES_PATH (for open_tv.py compatibility)
    CHROME_PROFILES_PATH = os.getenv('CHROME_PROFILES_PATH', os.getenv('CHROME_PROFILE_PATH', ''))
    CHROME_PROFILE_NAME = os.getenv('CHROME_PROFILE_NAME', 'Profile 3')

    # ===========================================
    # TradingView Chart URLs
    # ===========================================

    NWE_CHART_URL = os.getenv('NWE_CHART_URL', '')
    OBDIV_CHART_URL = os.getenv('OBDIV_CHART_URL', '')

    # ===========================================
    # Logging
    # ===========================================

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app_log.log')

    # ===========================================
    # Timing (seconds)
    # ===========================================

    NWE_BATCH_WAIT = int(os.getenv('NWE_BATCH_WAIT', 120))
    OBDIV_BATCH_WAIT = int(os.getenv('OBDIV_BATCH_WAIT', 30))
    SCREENSHOT_WAIT = int(os.getenv('SCREENSHOT_WAIT', 3))
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 60))

    # ===========================================
    # Batch Sizes
    # ===========================================

    NWE_BATCH_SIZE = int(os.getenv('NWE_BATCH_SIZE', 20))
    OBDIV_BATCH_SIZE = int(os.getenv('OBDIV_BATCH_SIZE', 8))
    SCREENSHOT_BATCH_SIZE = int(os.getenv('SCREENSHOT_BATCH_SIZE', 5))

    # ===========================================
    # Selenium Timeouts (seconds)
    # ===========================================

    SELENIUM_IMPLICIT_WAIT = int(os.getenv('SELENIUM_IMPLICIT_WAIT', 10))
    SELENIUM_EXPLICIT_WAIT = int(os.getenv('SELENIUM_EXPLICIT_WAIT', 30))
    PAGE_LOAD_TIMEOUT = int(os.getenv('PAGE_LOAD_TIMEOUT', 60))

    # ===========================================
    # Retry Configuration
    # ===========================================

    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', 5))

    # Exponential backoff delays (derived from RETRY_DELAY)
    @property
    def RETRY_DELAYS(self):
        """Returns list of retry delays with exponential backoff."""
        return [self.RETRY_DELAY * (2 ** i) for i in range(self.MAX_RETRIES)]

    # ===========================================
    # Validation
    # ===========================================

    @classmethod
    def validate(cls, strict: bool = True) -> bool:
        """
        Validate required configuration settings.

        Args:
            strict: If True, raises ValueError on missing required settings.
                   If False, logs warnings but returns False.

        Returns:
            True if all required settings are present, False otherwise.

        Raises:
            ValueError: If strict=True and required settings are missing.
        """
        errors = []
        warnings = []

        # Required settings
        if not cls.STOCK_BUDDY_API_URL:
            errors.append("STOCK_BUDDY_API_URL is required")

        if not cls.CHROME_PROFILES_PATH:
            errors.append("CHROME_PROFILES_PATH is required")
        else:
            # Check if TTE subfolder exists or can be created
            tte_path = os.path.join(cls.CHROME_PROFILES_PATH, 'TTE')
            if not os.path.exists(cls.CHROME_PROFILES_PATH):
                warnings.append(f"CHROME_PROFILES_PATH does not exist: {cls.CHROME_PROFILES_PATH}")

        # Recommended settings
        if not cls.NWE_CHART_URL:
            warnings.append("NWE_CHART_URL not set - NWE screener navigation will fail")

        if not cls.OBDIV_CHART_URL:
            warnings.append("OBDIV_CHART_URL not set - OBDIV screener navigation will fail")

        # Value range validation
        if cls.NWE_BATCH_SIZE > 20:
            warnings.append(f"NWE_BATCH_SIZE ({cls.NWE_BATCH_SIZE}) exceeds screener limit of 20")

        if cls.OBDIV_BATCH_SIZE > 8:
            warnings.append(f"OBDIV_BATCH_SIZE ({cls.OBDIV_BATCH_SIZE}) exceeds screener limit of 8")

        # Log warnings
        for warning in warnings:
            logger.warning(f"Config warning: {warning}")

        # Handle errors
        if errors:
            error_msg = f"Configuration errors: {', '.join(errors)}"
            if strict:
                raise ValueError(error_msg)
            else:
                logger.error(error_msg)
                return False

        return True

    @classmethod
    def print_config(cls):
        """Print current configuration (for debugging)."""
        print("\n=== TTE Configuration ===")
        print(f"API URL: {cls.STOCK_BUDDY_API_URL}")
        print(f"Chrome Profiles Path: {cls.CHROME_PROFILES_PATH}")
        print(f"Chrome Profile Name: {cls.CHROME_PROFILE_NAME}")
        print(f"NWE Chart URL: {cls.NWE_CHART_URL}")
        print(f"OBDIV Chart URL: {cls.OBDIV_CHART_URL}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"NWE Batch: {cls.NWE_BATCH_SIZE} symbols, {cls.NWE_BATCH_WAIT}s wait")
        print(f"OBDIV Batch: {cls.OBDIV_BATCH_SIZE} symbols, {cls.OBDIV_BATCH_WAIT}s wait")
        print(f"Retries: {cls.MAX_RETRIES} with delays {cls.RETRY_DELAYS}")
        print("=========================\n")


# Create singleton instance
config = Config()


# Convenience function for quick validation
def validate_config(strict: bool = True) -> bool:
    """Validate configuration. Shortcut for config.validate()."""
    return Config.validate(strict)


if __name__ == '__main__':
    # When run directly, print and validate config
    config.print_config()
    try:
        config.validate(strict=False)
        print("Configuration valid!")
    except ValueError as e:
        print(f"Configuration invalid: {e}")
