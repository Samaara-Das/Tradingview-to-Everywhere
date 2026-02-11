"""
Configuration for TTE Combo Mode.
Loads settings from combo_settings.yaml, with env var overrides for secrets.
"""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

SETTINGS_FILE = Path(__file__).parent / "combo_settings.yaml"


def _load_yaml() -> dict:
    """Load combo_settings.yaml and return as nested dict."""
    if not SETTINGS_FILE.exists():
        print(f"[WARNING] {SETTINGS_FILE} not found, using defaults", flush=True)
        return {}
    with open(SETTINGS_FILE, "r") as f:
        return yaml.safe_load(f) or {}


_yaml = _load_yaml()


@dataclass
class ComboConfig:
    """Configuration settings for the combo mode orchestrator."""

    # Chart settings
    layout_name: str = _yaml.get("chart", {}).get("layout_name", "Screener")
    chart_timeframe: str = _yaml.get("chart", {}).get("chart_timeframe", "1 hour")
    bar_style: str = _yaml.get("chart", {}).get("bar_style", "candle")
    headless: bool = _yaml.get("chart", {}).get("headless", False)

    # Screener indicator
    screener_shorttitle: str = _yaml.get("screener", {}).get("shorttitle", "Screener")
    screener_name: str = _yaml.get("screener", {}).get("name", "TTE Screener")

    # Alert creation
    batch_size: int = _yaml.get("alerts", {}).get("batch_size", 4)
    alert_creation_delay: float = _yaml.get("alerts", {}).get("creation_delay", 1.5)
    recalc_wait: float = _yaml.get("alerts", {}).get("recalc_wait", 2.0)

    # Webhook — env var takes precedence over yaml
    webhook_url: str = os.getenv(
        "COMBO_WEBHOOK_URL", _yaml.get("webhook", {}).get("url", "")
    )

    # Maintenance
    maintenance_interval: int = _yaml.get("maintenance", {}).get("interval", 300)

    # Progress tracking
    progress_file: str = _yaml.get("progress", {}).get("file", "combo_progress.json")

    # Stock Buddy API (future fallback)
    api_base_url: str = os.getenv(
        "STOCK_BUDDY_API_URL", "https://stock-buddy-app.vercel.app/api/tte"
    )
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))

    def validate(self) -> list[str]:
        """Validate required configuration. Returns list of error strings."""
        errors = []

        if not self.webhook_url:
            errors.append(
                "COMBO_WEBHOOK_URL is required (set in .env or combo_settings.yaml)"
            )

        if self.batch_size < 1 or self.batch_size > 4:
            errors.append("batch_size must be between 1 and 4 (TradingView hard limit)")

        if self.recalc_wait < 0.5:
            errors.append("recalc_wait must be at least 0.5 seconds")

        if self.maintenance_interval < 60:
            errors.append("maintenance_interval must be at least 60 seconds")

        valid_bar_styles = [
            "bar",
            "candle",
            "hollowCandle",
            "volCandles",
            "line",
            "lineWithMarkers",
            "stepline",
            "area",
            "hlcArea",
            "baseline",
            "column",
            "hilo",
            "ha",
            "renko",
            "pb",
            "kagi",
            "pnf",
            "range",
        ]
        if self.bar_style not in valid_bar_styles:
            errors.append(f"bar_style must be one of: {', '.join(valid_bar_styles)}")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0
