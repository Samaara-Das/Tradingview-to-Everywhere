"""
Configuration module for the TTE Tiered Orchestrator.
Loads settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration settings for the tiered orchestrator."""

    # Stock Buddy API
    api_base_url: str = os.getenv(
        "STOCK_BUDDY_API_URL", "https://stock-buddy-app.vercel.app/api/tte"
    )
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))

    # TradingView chart URLs
    nwe_chart_url: str = os.getenv("NWE_CHART_URL", "")
    obdiv_chart_url: str = os.getenv("OBDIV_CHART_URL", "")

    # Batch sizes (NWE screener supports max 20, OBDIV supports max 8)
    nwe_batch_size: int = int(os.getenv("NWE_BATCH_SIZE", "20"))
    obdiv_batch_size: int = int(os.getenv("OBDIV_BATCH_SIZE", "8"))

    # Wait times (seconds)
    nwe_batch_wait: int = int(os.getenv("NWE_BATCH_WAIT", "60"))
    obdiv_batch_wait: int = int(os.getenv("OBDIV_BATCH_WAIT", "30"))

    # Chrome settings
    chrome_profile: str = os.getenv("CHROME_PROFILE", "Profile 2")
    chrome_profiles_path: str = os.getenv("CHROME_PROFILES_PATH", "")
    headless: bool = os.getenv("HEADLESS", "false").lower() == "true"

    # Orchestrator settings
    cycle_interval: int = int(os.getenv("CYCLE_INTERVAL", "300"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay: int = int(os.getenv("RETRY_DELAY", "5"))

    # Screenshot settings
    screenshot_dir: str = os.getenv("SCREENSHOT_DIR", "screenshots")

    def validate(self) -> list[str]:
        """Validate required configuration. Returns list of missing/invalid fields."""
        errors = []

        if not self.api_base_url:
            errors.append("STOCK_BUDDY_API_URL is required")

        if not self.nwe_chart_url:
            errors.append("NWE_CHART_URL is required for Tier 1 operations")

        if not self.obdiv_chart_url:
            errors.append("OBDIV_CHART_URL is required for Tier 2 operations")

        if self.nwe_batch_size < 1 or self.nwe_batch_size > 20:
            errors.append(
                "NWE_BATCH_SIZE must be between 1 and 20 (TTE NWE Screener v2 limit)"
            )

        if self.obdiv_batch_size < 1 or self.obdiv_batch_size > 8:
            errors.append(
                "OBDIV_BATCH_SIZE must be between 1 and 8 (TTE OBDIV Screener v2 limit)"
            )

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0


# Global config instance
config = Config()
