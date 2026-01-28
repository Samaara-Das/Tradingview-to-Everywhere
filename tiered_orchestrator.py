"""
TTE Tiered Signal Orchestrator

This module implements a tiered approach to signal detection:
- Tier 1: NWE screeners run continuously in TradingView (lightweight, covers all symbols)
- Tier 2: When NWE triggers, this orchestrator uses Selenium to check OB/FVG and Divergence

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: NWE Screeners (Pine Script in TradingView)            │
│  - Multiple screeners, each watching 20 symbols                │
│  - Fires alerts: {"symbol":"XXX","nwe":"bullish","tf":"H4"}    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  THIS MODULE: Python Orchestrator                               │
│  - Receives NWE alerts from TradingView                        │
│  - Maintains "hot list" of symbols with active NWE signals     │
│  - Triggers Tier 2 checks (OB + Divergence) for hot symbols    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 2: Detailed Indicator Check (Selenium-driven)            │
│  - Opens chart for hot symbol                                  │
│  - Loads OB & FVG indicator → checks for overlap               │
│  - If OB found, loads Divergence indicator → checks signal     │
│  - Fires final trading signal if all conditions met            │
└─────────────────────────────────────────────────────────────────┘

Usage:
    orchestrator = TieredOrchestrator(driver)

    # When NWE alert received from TradingView
    orchestrator.on_nwe_alert({"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4"})

    # Periodically process hot list
    orchestrator.process_hot_symbols()
"""

import logger_setup
from time import sleep, time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from json import loads, dumps
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Set up logger
orchestrator_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)


class SignalDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class HotSymbol:
    """Represents a symbol that has triggered NWE and needs further analysis."""
    symbol: str
    direction: SignalDirection
    timeframes: List[str]  # Which TFs triggered: ["H4", "D1"]
    nwe_triggered_at: datetime
    ob_checked: bool = False
    ob_found: bool = False
    ob_timeframe: Optional[str] = None
    div_checked: bool = False
    div_found: bool = False
    div_timeframe: Optional[str] = None
    last_checked: Optional[datetime] = None
    check_count: int = 0

    def needs_recheck(self, recheck_interval_minutes: int = 60) -> bool:
        """Check if symbol needs to be rechecked (NWE zones can persist for hours)."""
        if self.last_checked is None:
            return True
        elapsed = datetime.now() - self.last_checked
        return elapsed > timedelta(minutes=recheck_interval_minutes)

    def is_expired(self, expiry_hours: int = 24) -> bool:
        """Check if this hot symbol entry has expired."""
        elapsed = datetime.now() - self.nwe_triggered_at
        return elapsed > timedelta(hours=expiry_hours)


@dataclass
class Tier2Result:
    """Result from a Tier 2 (OB + Divergence) check."""
    symbol: str
    direction: SignalDirection
    ob_found: bool
    ob_timeframe: Optional[str] = None
    ob_type: Optional[str] = None  # "OB", "FVG", "Breaker"
    div_found: bool = False
    div_timeframe: Optional[str] = None
    div_type: Optional[str] = None  # "Logic2", "Internal"
    signal_level: int = 0  # 1=NWE, 2=NWE+OB, 3=NWE+OB+DIV
    error: Optional[str] = None


class TieredOrchestrator:
    """
    Orchestrates the tiered signal detection process.

    Tier 1 (NWE) runs in TradingView and fires alerts to this module.
    Tier 2 (OB + DIV) is triggered by this module using Selenium.
    """

    # Indicator short titles (must match what's in TradingView)
    OB_FVG_INDICATOR = "OB & FVG"
    DIVERGENCE_INDICATOR = "Kernel AO Div"

    # Timeframes to check for OB/DIV (in order of priority)
    OB_TIMEFRAMES = ["240", "D", "W"]  # H4, D1, W1
    DIV_TIMEFRAMES = ["240", "D"]  # H4, D1

    def __init__(self, driver, chart_handler=None):
        """
        Initialize the orchestrator.

        Args:
            driver: Selenium WebDriver instance
            chart_handler: Optional OpenChart instance for chart operations
        """
        self.driver = driver
        self.chart_handler = chart_handler
        self.hot_list: Dict[str, HotSymbol] = {}  # symbol -> HotSymbol
        self.processed_signals: List[Tier2Result] = []
        self.last_cleanup = datetime.now()

        orchestrator_logger.info("TieredOrchestrator initialized")

    def on_nwe_alert(self, alert_data: dict) -> None:
        """
        Handle incoming NWE alert from TradingView.

        Expected format: {"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4,D1"}

        Args:
            alert_data: Parsed JSON alert from TradingView NWE screener
        """
        try:
            symbol = alert_data.get("symbol", "").upper()
            direction_str = alert_data.get("nwe", "").lower()
            tf_str = alert_data.get("tf", "")

            if not symbol or not direction_str:
                orchestrator_logger.warning(f"Invalid NWE alert data: {alert_data}")
                return

            direction = SignalDirection.BULLISH if direction_str == "bullish" else SignalDirection.BEARISH
            timeframes = [tf.strip() for tf in tf_str.split(",") if tf.strip()]

            # Add or update in hot list
            if symbol in self.hot_list:
                # Update existing entry
                existing = self.hot_list[symbol]
                existing.direction = direction
                existing.timeframes = timeframes
                existing.nwe_triggered_at = datetime.now()
                # Reset check flags for new direction
                existing.ob_checked = False
                existing.ob_found = False
                existing.div_checked = False
                existing.div_found = False
                orchestrator_logger.info(f"Updated hot list: {symbol} -> {direction.value} on {timeframes}")
            else:
                # New entry
                self.hot_list[symbol] = HotSymbol(
                    symbol=symbol,
                    direction=direction,
                    timeframes=timeframes,
                    nwe_triggered_at=datetime.now()
                )
                orchestrator_logger.info(f"Added to hot list: {symbol} -> {direction.value} on {timeframes}")

            # Cleanup expired entries periodically
            self._cleanup_expired()

        except Exception as e:
            orchestrator_logger.exception(f"Error processing NWE alert: {e}")

    def remove_from_hot_list(self, symbol: str) -> None:
        """
        Remove a symbol from the hot list (e.g., when NWE signal ends).

        Args:
            symbol: Symbol to remove
        """
        if symbol in self.hot_list:
            del self.hot_list[symbol]
            orchestrator_logger.info(f"Removed from hot list: {symbol}")

    def get_hot_symbols(self) -> List[HotSymbol]:
        """Get all symbols currently in the hot list."""
        return list(self.hot_list.values())

    def get_symbols_needing_check(self) -> List[HotSymbol]:
        """Get symbols that need Tier 2 checking."""
        return [
            hs for hs in self.hot_list.values()
            if hs.needs_recheck() and not hs.is_expired()
        ]

    def process_hot_symbols(self) -> List[Tier2Result]:
        """
        Process all hot symbols that need Tier 2 checking.

        Returns:
            List of Tier2Result for symbols that completed full signal chain
        """
        results = []
        symbols_to_check = self.get_symbols_needing_check()

        orchestrator_logger.info(f"Processing {len(symbols_to_check)} hot symbols")

        for hot_symbol in symbols_to_check:
            try:
                result = self._check_tier2(hot_symbol)
                if result:
                    results.append(result)
                    if result.signal_level >= 2:  # At least NWE + OB
                        self.processed_signals.append(result)
            except Exception as e:
                orchestrator_logger.exception(f"Error checking {hot_symbol.symbol}: {e}")

        return results

    def _check_tier2(self, hot_symbol: HotSymbol) -> Optional[Tier2Result]:
        """
        Perform Tier 2 check (OB + Divergence) for a hot symbol.

        Args:
            hot_symbol: The symbol to check

        Returns:
            Tier2Result with findings, or None if check failed
        """
        symbol = hot_symbol.symbol
        direction = hot_symbol.direction

        orchestrator_logger.info(f"Starting Tier 2 check for {symbol} ({direction.value})")

        result = Tier2Result(
            symbol=symbol,
            direction=direction,
            ob_found=False,
            signal_level=1  # Already has NWE (that's why it's in hot list)
        )

        try:
            # Step 1: Navigate to symbol chart
            if not self._navigate_to_symbol(symbol):
                result.error = "Failed to navigate to symbol"
                return result

            # Step 2: Check OB/FVG on each timeframe
            for tf in self.OB_TIMEFRAMES:
                if not self._change_timeframe(tf):
                    continue

                ob_result = self._check_ob_indicator(direction)
                if ob_result:
                    result.ob_found = True
                    result.ob_timeframe = tf
                    result.ob_type = ob_result.get("type", "OB")
                    result.signal_level = 2
                    orchestrator_logger.info(f"{symbol}: OB found on {tf}")
                    break

            hot_symbol.ob_checked = True
            hot_symbol.ob_found = result.ob_found
            hot_symbol.ob_timeframe = result.ob_timeframe

            # Step 3: If OB found, check Divergence
            if result.ob_found:
                for tf in self.DIV_TIMEFRAMES:
                    if not self._change_timeframe(tf):
                        continue

                    div_result = self._check_divergence_indicator(direction)
                    if div_result:
                        result.div_found = True
                        result.div_timeframe = tf
                        result.div_type = div_result.get("type", "Logic2")
                        result.signal_level = 3
                        orchestrator_logger.info(f"{symbol}: Divergence found on {tf}")
                        break

                hot_symbol.div_checked = True
                hot_symbol.div_found = result.div_found
                hot_symbol.div_timeframe = result.div_timeframe

            # Update check timestamp
            hot_symbol.last_checked = datetime.now()
            hot_symbol.check_count += 1

            orchestrator_logger.info(
                f"Tier 2 complete for {symbol}: Level {result.signal_level} "
                f"(OB: {result.ob_found}, DIV: {result.div_found})"
            )

            return result

        except Exception as e:
            result.error = str(e)
            orchestrator_logger.exception(f"Tier 2 check failed for {symbol}: {e}")
            return result

    def _navigate_to_symbol(self, symbol: str) -> bool:
        """
        Navigate TradingView chart to the specified symbol.

        Args:
            symbol: Symbol to navigate to (e.g., "GBPAUD")

        Returns:
            True if successful
        """
        try:
            if self.chart_handler:
                return self.chart_handler.change_symbol(symbol)

            # Fallback: Direct Selenium implementation
            symbol_search = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"]')
                )
            )

            current_symbol = symbol_search.find_element(By.CSS_SELECTOR, "div").text
            if current_symbol.upper() == symbol.upper():
                return True  # Already on this symbol

            symbol_search.click()
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[data-role="search"]')
                )
            )

            ActionChains(self.driver).key_down(Keys.CONTROL, search_input).send_keys("a").perform()
            search_input.send_keys(Keys.DELETE)
            search_input.send_keys(symbol)
            search_input.send_keys(Keys.ENTER)

            sleep(2)  # Wait for chart to load
            return True

        except Exception as e:
            orchestrator_logger.exception(f"Failed to navigate to {symbol}: {e}")
            return False

    def _change_timeframe(self, timeframe: str) -> bool:
        """
        Change chart timeframe.

        Args:
            timeframe: Timeframe code ("240" for H4, "D" for Daily, "W" for Weekly)

        Returns:
            True if successful
        """
        try:
            if self.chart_handler:
                # Convert timeframe code to display format
                tf_map = {"240": "4h", "D": "1D", "W": "1W"}
                return self.chart_handler.change_tframe(tf_map.get(timeframe, timeframe))

            # Fallback: Direct Selenium implementation
            tf_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[id="header-toolbar-intervals"]')
                )
            )

            tf_button.click()
            sleep(0.5)

            # Find and click the matching timeframe
            tf_options = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[data-value]'
            )

            tf_map = {"240": "240", "D": "1D", "W": "1W"}
            target_value = tf_map.get(timeframe, timeframe)

            for option in tf_options:
                if option.get_attribute("data-value") == target_value:
                    option.click()
                    sleep(1)  # Wait for chart to update
                    return True

            # Close dropdown if timeframe not found
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            return False

        except Exception as e:
            orchestrator_logger.exception(f"Failed to change timeframe to {timeframe}: {e}")
            return False

    def _check_ob_indicator(self, direction: SignalDirection) -> Optional[dict]:
        """
        Check if OB & FVG indicator shows overlap for the given direction.

        This method needs to be implemented based on how your OB & FVG indicator
        displays its output (table, labels, plots, etc.)

        Args:
            direction: SignalDirection to check for

        Returns:
            Dict with OB info if found, None otherwise
        """
        try:
            # TODO: Implement based on your OB & FVG indicator's output format
            # Options:
            # 1. Read from indicator's debug table
            # 2. Check for specific label colors/positions
            # 3. Use indicator's alert output
            # 4. Parse Data Window values

            # Placeholder implementation - you'll need to customize this
            # based on how your OB & FVG indicator displays results

            # Example: Check if indicator is showing an overlap
            # This is a simplified example - actual implementation depends on your indicator

            indicator = self._find_indicator(self.OB_FVG_INDICATOR)
            if not indicator:
                orchestrator_logger.warning(f"OB indicator not found on chart")
                return None

            # Wait for indicator to load
            sleep(1)

            # Check indicator output (customize based on your indicator)
            # For now, return None (no OB found) as placeholder
            return None

        except Exception as e:
            orchestrator_logger.exception(f"Error checking OB indicator: {e}")
            return None

    def _check_divergence_indicator(self, direction: SignalDirection) -> Optional[dict]:
        """
        Check if Divergence indicator shows a signal for the given direction.

        This method needs to be implemented based on how your Kernel AO Divergence
        indicator displays its output.

        Args:
            direction: SignalDirection to check for

        Returns:
            Dict with divergence info if found, None otherwise
        """
        try:
            # TODO: Implement based on your Divergence indicator's output format

            indicator = self._find_indicator(self.DIVERGENCE_INDICATOR)
            if not indicator:
                orchestrator_logger.warning(f"Divergence indicator not found on chart")
                return None

            # Wait for indicator to load
            sleep(1)

            # Check indicator output (customize based on your indicator)
            # For now, return None (no divergence found) as placeholder
            return None

        except Exception as e:
            orchestrator_logger.exception(f"Error checking Divergence indicator: {e}")
            return None

    def _find_indicator(self, indicator_name: str):
        """
        Find an indicator on the chart by its short title.

        Args:
            indicator_name: The indicator's short title

        Returns:
            WebElement of the indicator, or None if not found
        """
        try:
            indicators = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')
                )
            )

            for ind in indicators:
                title_elem = ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]')
                if title_elem.text == indicator_name:
                    return ind

            return None

        except Exception as e:
            orchestrator_logger.exception(f"Error finding indicator {indicator_name}: {e}")
            return None

    def _cleanup_expired(self) -> None:
        """Remove expired entries from the hot list."""
        now = datetime.now()
        if (now - self.last_cleanup) < timedelta(minutes=30):
            return  # Don't cleanup too frequently

        expired = [
            symbol for symbol, hs in self.hot_list.items()
            if hs.is_expired()
        ]

        for symbol in expired:
            del self.hot_list[symbol]
            orchestrator_logger.info(f"Expired from hot list: {symbol}")

        self.last_cleanup = now

    def get_statistics(self) -> dict:
        """Get orchestrator statistics."""
        return {
            "hot_list_size": len(self.hot_list),
            "bullish_count": sum(1 for hs in self.hot_list.values() if hs.direction == SignalDirection.BULLISH),
            "bearish_count": sum(1 for hs in self.hot_list.values() if hs.direction == SignalDirection.BEARISH),
            "needs_check": len(self.get_symbols_needing_check()),
            "processed_signals": len(self.processed_signals),
            "level_3_signals": sum(1 for r in self.processed_signals if r.signal_level == 3),
        }

    def to_json(self) -> str:
        """Export hot list to JSON for persistence."""
        data = {
            "hot_list": [
                {
                    "symbol": hs.symbol,
                    "direction": hs.direction.value,
                    "timeframes": hs.timeframes,
                    "nwe_triggered_at": hs.nwe_triggered_at.isoformat(),
                    "ob_checked": hs.ob_checked,
                    "ob_found": hs.ob_found,
                    "div_checked": hs.div_checked,
                    "div_found": hs.div_found,
                }
                for hs in self.hot_list.values()
            ],
            "exported_at": datetime.now().isoformat()
        }
        return dumps(data, indent=2)

    def from_json(self, json_str: str) -> None:
        """Import hot list from JSON."""
        try:
            data = loads(json_str)
            for item in data.get("hot_list", []):
                symbol = item["symbol"]
                self.hot_list[symbol] = HotSymbol(
                    symbol=symbol,
                    direction=SignalDirection(item["direction"]),
                    timeframes=item["timeframes"],
                    nwe_triggered_at=datetime.fromisoformat(item["nwe_triggered_at"]),
                    ob_checked=item.get("ob_checked", False),
                    ob_found=item.get("ob_found", False),
                    div_checked=item.get("div_checked", False),
                    div_found=item.get("div_found", False),
                )
            orchestrator_logger.info(f"Loaded {len(self.hot_list)} symbols from JSON")
        except Exception as e:
            orchestrator_logger.exception(f"Error loading from JSON: {e}")


# Example usage and integration with existing TTE system
if __name__ == "__main__":
    print("TTE Tiered Orchestrator")
    print("=" * 50)
    print("\nThis module provides:")
    print("1. Hot list management for symbols with NWE signals")
    print("2. Tier 2 checking (OB + Divergence) via Selenium")
    print("3. Signal level tracking (1=NWE, 2=NWE+OB, 3=NWE+OB+DIV)")
    print("\nIntegration:")
    print("- Tier 1 NWE screeners run in TradingView")
    print("- This orchestrator receives NWE alerts and manages hot list")
    print("- Periodically runs Tier 2 checks on hot symbols")
    print("\nNote: _check_ob_indicator() and _check_divergence_indicator()")
    print("need to be implemented based on your indicator's output format.")
