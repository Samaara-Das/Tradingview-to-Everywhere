"""
TTE Tiered Orchestrator

Manages the two-tier symbol scanning workflow:
1. Phase 1 (NWE): Scans batches of symbols for NWE zones
2. Phase 2 (OBDIV): Processes hot symbols through OBDIV analysis

This module coordinates between the Stock Buddy API and TradingView browser automation.
"""

import logging
import time
from typing import List, Optional

from api_client import StockBuddyAPIClient
from config import Config

logger = logging.getLogger(__name__)


# TTE Screener indicator names (as they appear in TradingView)
NWE_SCREENER_SHORTTITLE = "TTE NWE Screener"
NWE_SCREENER_NAME = "TTE NWE Screener"
OBDIV_SCREENER_SHORTTITLE = "TTE OBDIV Screener"
OBDIV_SCREENER_NAME = "TTE OBDIV Screener"

# Layout names for saved TradingView layouts
NWE_LAYOUT_NAME = "NWE"
OBDIV_LAYOUT_NAME = "OBDIV"

# Webhook URLs (relative to API base)
NWE_WEBHOOK_PATH = "/nwe"
OBDIV_WEBHOOK_PATH = "/obdiv"


class TieredOrchestrator:
    """
    Orchestrates the tiered symbol scanning workflow.

    The orchestrator manages the following cycle:
    1. Fetch a batch of symbols from the API
    2. Input symbols into NWE screener and create webhook alert
    3. Wait for webhook to fire (screener sends data)
    4. Delete alert and mark symbols as scanned
    5. Fetch hot symbols (those with NWE triggers)
    6. Switch to OBDIV layout and process hot symbols in batches
    7. Return to NWE layout and repeat
    """

    def __init__(
        self,
        browser,
        api_client: StockBuddyAPIClient,
        config: Config,
    ):
        """
        Initialize the orchestrator.

        Args:
            browser: Selenium browser instance with TradingView automation methods
            api_client: Stock Buddy API client
            config: Configuration settings
        """
        self.browser = browser
        self.api = api_client
        self.config = config
        self.running = False

        # Track first-switch state for layout initialization
        self._nwe_layout_initialized = False
        self._obdiv_layout_initialized = False

        # Build webhook URLs
        api_base = config.api_base_url.rstrip("/")
        # Webhook URLs should be at the same base as the API
        self.nwe_webhook_url = f"{api_base}{NWE_WEBHOOK_PATH}"
        self.obdiv_webhook_url = f"{api_base}{OBDIV_WEBHOOK_PATH}"

        logger.info(f"NWE Webhook URL: {self.nwe_webhook_url}")
        logger.info(f"OBDIV Webhook URL: {self.obdiv_webhook_url}")

    def run(self, single_cycle: bool = False):
        """
        Run the main orchestration loop.

        Args:
            single_cycle: If True, run only one cycle then stop
        """
        self.running = True
        cycle_count = 0

        logger.info("Starting tiered orchestrator...")

        while self.running:
            cycle_count += 1
            logger.info(f"=== Starting cycle #{cycle_count} ===")

            try:
                # Phase 1: NWE Batch Processing
                self._phase1_nwe_batch()

                # Phase 2: OBDIV Processing
                had_hot_symbols = self._phase2_obdiv_processing()

                logger.info(f"=== Completed cycle #{cycle_count} ===")

                if single_cycle:
                    logger.info("Single cycle mode - stopping orchestrator")
                    print("[DEBUG] Single cycle complete - stopping", flush=True)
                    break

                # Continue immediately to next cycle (no waiting)
                print(
                    "[DEBUG] Cycle complete - starting next cycle immediately",
                    flush=True,
                )

            except Exception as e:
                logger.exception(f"Error in cycle #{cycle_count}: {e}")
                # Continue to next cycle after a delay
                time.sleep(self.config.retry_delay)

    def stop(self):
        """Stop the orchestrator gracefully."""
        logger.info("Stopping orchestrator...")
        self.running = False

    def _switch_to_layout_with_setup(
        self, layout_name: str, is_first_switch: bool
    ) -> bool:
        """
        Switch to a layout with retry logic. Always sets timeframe. On first switch, also saves layout.

        Args:
            layout_name: "NWE" or "OBDIV"
            is_first_switch: If True, also save layout after setup

        Returns:
            True if successful, False otherwise
        """
        print(
            f"[DEBUG] _switch_to_layout_with_setup: Switching to layout '{layout_name}'",
            flush=True,
        )

        # Save current layout before switching
        print("[DEBUG] Saving current layout before switching...", flush=True)
        self.browser.save_layout()
        time.sleep(1)  # Brief pause to ensure save completes

        # Try to change layout (with retry)
        print(f"[DEBUG] Calling browser.change_layout('{layout_name}')...", flush=True)
        result = self.browser.change_layout(layout_name)
        print(f"[DEBUG] change_layout returned: {result}", flush=True)

        if not result:
            print(f"[DEBUG] First attempt failed, retrying...", flush=True)
            self.browser.change_layout(layout_name)  # retry
            current = self.browser.current_layout()
            print(f"[DEBUG] After retry, current_layout() = '{current}'", flush=True)
            if current != layout_name:
                logger.error(f"Cannot change layout to {layout_name}")
                return False

        # Wait for layout to fully load (indicators need time to appear)
        print(
            f"[DEBUG] Waiting 5s for layout '{layout_name}' to fully load...",
            flush=True,
        )
        time.sleep(5)

        # Verify the layout actually changed
        current = self.browser.current_layout()
        print(f"[DEBUG] After wait, current_layout() = '{current}'", flush=True)
        if current != layout_name:
            logger.error(f"Layout mismatch: expected '{layout_name}', got '{current}'")
            # Try one more time
            print(f"[DEBUG] Layout mismatch, trying change_layout again...", flush=True)
            self.browser.change_layout(layout_name)
            time.sleep(3)
            current = self.browser.current_layout()
            if current != layout_name:
                logger.error(
                    f"Cannot change layout to {layout_name} after multiple attempts"
                )
                return False

        print(f"[DEBUG] Layout successfully set to '{layout_name}'", flush=True)

        # Always set timeframe to "5 minutes" (lowest timeframe for faster alert triggers)
        CHART_TIMEFRAME = "5 minutes"
        # Force timeframe change by using the dedicated method
        if not self.browser.open_chart.force_change_tframe(CHART_TIMEFRAME):
            logger.warning(f"force_change_tframe failed, trying regular change_tframe")
            if not self.browser.open_chart.change_tframe(CHART_TIMEFRAME):
                logger.error(f"Cannot change timeframe to {CHART_TIMEFRAME}")
                return False

        logger.info(f"Chart timeframe set to {CHART_TIMEFRAME}")

        # Save the layout only on first switch
        if is_first_switch:
            if not self.browser.save_layout():
                self.browser.save_layout()  # retry (non-critical)
                logger.warning(f"Could not save layout {layout_name}")
            else:
                logger.info(f"Saved layout {layout_name}")

        return True

    def _phase1_nwe_batch(self):
        """
        Phase 1: NWE Batch Processing

        1. Fetch next batch of symbols from API
        2. Input symbols into NWE screener
        3. Create webhook alert
        4. Wait for webhook to fire
        5. Delete alert
        6. Mark symbols as scanned
        """
        logger.info("--- Phase 1: NWE Batch Processing ---")

        # Get next batch of symbols
        batch_response = self.api.get_next_symbol_batch(self.config.nwe_batch_size)

        if not batch_response.get("success", False):
            logger.error(
                f"Failed to get symbol batch: {batch_response.get('error', 'Unknown error')}"
            )
            return

        symbols = batch_response.get("batch", [])
        if not symbols:
            logger.info("No symbols in batch - skipping NWE phase")
            return

        # Extract just the symbol strings from the batch
        symbol_strings = [s["symbol"] if isinstance(s, dict) else s for s in symbols]
        batch_number = batch_response.get("batch_number", "?")

        logger.info(
            f"Processing NWE batch #{batch_number} with {len(symbol_strings)} symbols"
        )

        try:
            # Ensure we're on the NWE layout (with setup on first switch)
            is_first = not self._nwe_layout_initialized
            if not self._switch_to_layout_with_setup(NWE_LAYOUT_NAME, is_first):
                logger.error("Could not switch to NWE layout")
                return
            self._nwe_layout_initialized = True

            # Input symbols into the NWE screener
            if not self._input_symbols_to_screener(
                symbol_strings, NWE_SCREENER_SHORTTITLE
            ):
                logger.error("Failed to input symbols into NWE screener")
                return

            # Give the screener time to recalculate
            time.sleep(3)

            # Click on the NWE screener indicator to select it before creating alert
            nwe_indicator = self.browser._safe_indicator_access(NWE_SCREENER_SHORTTITLE)
            if not nwe_indicator:
                logger.error("Could not find NWE screener indicator")
                return
            nwe_indicator.click()
            logger.info(f"Clicked on {NWE_SCREENER_SHORTTITLE} indicator")

            # Create webhook alert for NWE screener
            success, error_type = self.browser.create_webhook_alert(
                NWE_SCREENER_SHORTTITLE, self.nwe_webhook_url
            )
            if not success:
                if error_type == "data_subscription":
                    logger.warning(
                        f"Data subscription error for NWE batch - marking {len(symbol_strings)} symbols as scanned and skipping"
                    )
                    print(
                        f"[DEBUG] Data subscription error - marking symbols as scanned",
                        flush=True,
                    )
                    self.api.mark_symbols_scanned(symbol_strings)
                else:
                    logger.error("Failed to create webhook alert for NWE screener")
                return

            logger.info(
                f"Waiting up to {self.config.nwe_batch_wait}s for NWE webhook to fire..."
            )
            print(
                f"[DEBUG] Starting monitored wait (max {self.config.nwe_batch_wait}s) for NWE webhook...",
                flush=True,
            )
            webhook_detected, actual_wait = (
                self.browser.wait_for_webhook_with_monitoring(
                    screener_name=NWE_SCREENER_SHORTTITLE,
                    max_wait_seconds=self.config.nwe_batch_wait,
                )
            )
            if webhook_detected:
                logger.info(f"NWE webhook detected after {actual_wait:.1f}s")
                print(
                    f"[DEBUG] NWE webhook detected after {actual_wait:.1f}s", flush=True
                )
            else:
                logger.warning(f"NWE webhook wait timed out after {actual_wait:.1f}s")
                print(
                    f"[DEBUG] NWE webhook wait timed out after {actual_wait:.1f}s",
                    flush=True,
                )

            # Delete the alert
            print("[DEBUG] Calling delete_all_alerts()...", flush=True)
            if not self.browser.delete_all_alerts():
                logger.warning("Failed to delete alerts, continuing anyway...")
                print("[DEBUG] delete_all_alerts() returned False", flush=True)
            else:
                print("[DEBUG] delete_all_alerts() returned True", flush=True)

            # Mark symbols as scanned
            print("[DEBUG] Calling api.mark_symbols_scanned()...", flush=True)
            mark_response = self.api.mark_symbols_scanned(symbol_strings)
            print(f"[DEBUG] mark_symbols_scanned response: {mark_response}", flush=True)
            if mark_response.get("success", False):
                logger.info(f"Marked {len(symbol_strings)} symbols as scanned")
            else:
                logger.warning(
                    f"Failed to mark symbols as scanned: {mark_response.get('error', 'Unknown error')}"
                )

            # Save the NWE layout after Phase 1 completes
            print("[DEBUG] Saving NWE layout after Phase 1...", flush=True)
            self.browser.save_layout()
            time.sleep(1)
            print("[DEBUG] NWE layout saved", flush=True)

            print("[DEBUG] Phase 1 NWE batch complete", flush=True)

        except Exception as e:
            logger.exception(f"Error in Phase 1: {e}")
            # Try to clean up alerts
            try:
                self.browser.delete_all_alerts()
            except:
                pass

    def _phase2_obdiv_processing(self) -> bool:
        """
        Phase 2: OBDIV Processing

        1. Fetch hot symbols from API
        2. Switch to OBDIV layout
        3. Process hot symbols in batches
        4. Switch back to NWE layout

        Returns:
            True if hot symbols were found and processed, False otherwise
        """
        print("[DEBUG] === Entering Phase 2: OBDIV Processing ===", flush=True)
        logger.info("--- Phase 2: OBDIV Processing ---")

        # Get hot symbols pending Tier 2 processing
        print("[DEBUG] Fetching hot symbols from API...", flush=True)
        hot_symbols = self.api.get_hot_symbols(limit=50)  # Get more, we'll batch them
        print(f"[DEBUG] get_hot_symbols returned: {hot_symbols}", flush=True)

        if not hot_symbols:
            logger.info("No hot symbols to process - skipping OBDIV phase")
            print("[DEBUG] No hot symbols - skipping OBDIV phase", flush=True)
            return False

        logger.info(f"Found {len(hot_symbols)} hot symbols for OBDIV processing")

        try:
            # Switch to OBDIV layout (with setup on first switch)
            is_first = not self._obdiv_layout_initialized
            print(
                f"[DEBUG] Switching to OBDIV layout (is_first={is_first})...",
                flush=True,
            )
            if not self._switch_to_layout_with_setup(OBDIV_LAYOUT_NAME, is_first):
                logger.error("Could not switch to OBDIV layout")
                return False
            self._obdiv_layout_initialized = True
            print("[DEBUG] OBDIV layout switch complete", flush=True)

            # Wait for OBDIV indicator to be available
            print(
                f"[DEBUG] Waiting for {OBDIV_SCREENER_SHORTTITLE} indicator to appear...",
                flush=True,
            )
            max_wait = 10
            indicator_found = False
            for i in range(max_wait):
                indicator = self.browser._safe_indicator_access(
                    OBDIV_SCREENER_SHORTTITLE
                )
                if indicator:
                    print(
                        f"[DEBUG] Found {OBDIV_SCREENER_SHORTTITLE} indicator after {i+1}s",
                        flush=True,
                    )
                    indicator_found = True
                    break
                print(
                    f"[DEBUG] Indicator not found, waiting... ({i+1}/{max_wait})",
                    flush=True,
                )
                time.sleep(1)

            if not indicator_found:
                logger.error(
                    f"Could not find {OBDIV_SCREENER_SHORTTITLE} indicator after {max_wait}s"
                )
                return False

            # Process hot symbols in batches
            batch_size = self.config.obdiv_batch_size
            processed_count = 0

            while hot_symbols:
                # Take a batch
                batch = hot_symbols[:batch_size]
                hot_symbols = hot_symbols[batch_size:]

                # Extract symbol strings
                symbol_strings = [
                    s["symbol"] if isinstance(s, dict) else s for s in batch
                ]

                logger.info(f"Processing OBDIV batch of {len(symbol_strings)} symbols")

                # Input symbols into OBDIV screener
                if not self._input_symbols_to_screener(
                    symbol_strings, OBDIV_SCREENER_SHORTTITLE
                ):
                    logger.error("Failed to input symbols into OBDIV screener")
                    continue

                # Give the screener time to recalculate
                time.sleep(3)

                # Click on the OBDIV screener indicator to select it before creating alert
                obdiv_indicator = self.browser._safe_indicator_access(
                    OBDIV_SCREENER_SHORTTITLE
                )
                if not obdiv_indicator:
                    logger.error("Could not find OBDIV screener indicator")
                    continue
                obdiv_indicator.click()
                logger.info(f"Clicked on {OBDIV_SCREENER_SHORTTITLE} indicator")

                # Create webhook alert for OBDIV screener
                success, error_type = self.browser.create_webhook_alert(
                    OBDIV_SCREENER_SHORTTITLE, self.obdiv_webhook_url
                )
                if not success:
                    if error_type == "data_subscription":
                        logger.warning(
                            f"Data subscription error for OBDIV batch - skipping to next batch"
                        )
                    else:
                        logger.error(
                            "Failed to create webhook alert for OBDIV screener"
                        )
                    continue

                logger.info(
                    f"Waiting up to {self.config.obdiv_batch_wait}s for OBDIV webhook to fire..."
                )
                webhook_detected, actual_wait = (
                    self.browser.wait_for_webhook_with_monitoring(
                        screener_name=OBDIV_SCREENER_SHORTTITLE,
                        max_wait_seconds=self.config.obdiv_batch_wait,
                    )
                )
                if webhook_detected:
                    logger.info(f"OBDIV webhook detected after {actual_wait:.1f}s")
                else:
                    logger.warning(
                        f"OBDIV webhook wait timed out after {actual_wait:.1f}s"
                    )

                # Delete the alert
                if not self.browser.delete_all_alerts():
                    logger.warning("Failed to delete alerts, continuing anyway...")

                processed_count += len(symbol_strings)

            # Save the OBDIV layout after Phase 2 completes
            print("[DEBUG] Saving OBDIV layout after Phase 2...", flush=True)
            self.browser.save_layout()
            time.sleep(1)
            print("[DEBUG] OBDIV layout saved", flush=True)

            logger.info(f"Completed OBDIV processing for {processed_count} symbols")
            return True

        except Exception as e:
            logger.exception(f"Error in Phase 2: {e}")
            # Try to clean up alerts
            try:
                self.browser.delete_all_alerts()
            except:
                pass
            return False
        finally:
            # Always try to switch back to NWE layout and save it
            try:
                print("[DEBUG] Switching back to NWE layout...", flush=True)
                self.browser.change_layout(NWE_LAYOUT_NAME)
                time.sleep(1)
                self.browser.save_layout()
                time.sleep(1)
                print("[DEBUG] Switched back to NWE layout and saved", flush=True)
            except:
                logger.warning("Could not switch back to NWE layout")

    def _input_symbols_to_screener(
        self, symbols: List[str], screener_shorttitle: str
    ) -> bool:
        """
        Input symbols into a screener's settings.

        Args:
            symbols: List of symbol strings
            screener_shorttitle: The screener's short title

        Returns:
            True if successful, False otherwise
        """
        try:
            # The change_settings method in open_tv.py handles opening the indicator
            # settings dialog and filling in the symbol inputs
            return self.browser.change_settings(symbols, screener_shorttitle)
        except Exception as e:
            logger.exception(f"Failed to input symbols to {screener_shorttitle}: {e}")
            return False


def create_orchestrator(config: Optional[Config] = None) -> TieredOrchestrator:
    """
    Factory function to create a fully initialized orchestrator.

    This handles the setup of all components:
    - Configuration loading
    - API client initialization
    - Browser initialization

    Args:
        config: Optional config instance. If None, creates from environment.

    Returns:
        Initialized TieredOrchestrator instance
    """
    from config import config as default_config
    import logger_setup
    from open_tv import Browser
    from env import PROFILE
    from os import getenv

    if config is None:
        config = default_config

    print("[DEBUG] create_orchestrator() started", flush=True)

    # Validate configuration
    print("[DEBUG] Validating configuration...", flush=True)
    errors = config.validate()
    if errors:
        raise ValueError(f"Configuration errors: {errors}")
    print("[DEBUG] Configuration valid", flush=True)

    # Initialize API client
    print("[DEBUG] Initializing API client...", flush=True)
    api_client = StockBuddyAPIClient(
        base_url=config.api_base_url, timeout=config.api_timeout
    )

    # Check API health
    print("[DEBUG] Checking API health...", flush=True)
    if not api_client.health_check():
        logger.warning("API health check failed - proceeding anyway")
        print("[DEBUG] API health check failed (continuing anyway)", flush=True)
    else:
        print("[DEBUG] API health check passed", flush=True)

    # Delete expired hot symbols at startup
    print("[DEBUG] Deleting expired hot symbols...", flush=True)
    result = api_client.delete_expired_hot_symbols()
    if result.get("success"):
        deleted = result.get("deleted_count", 0)
        print(f"[DEBUG] Deleted {deleted} expired hot symbols", flush=True)
        logger.info(f"Deleted {deleted} expired hot symbols at startup")
    else:
        print(
            f"[DEBUG] Warning: Failed to delete expired symbols: {result.get('error')}",
            flush=True,
        )
        logger.warning(f"Failed to delete expired hot symbols: {result.get('error')}")

    # Initialize browser
    # For the tiered orchestrator, we use placeholder values for the legacy screener params
    # since we only need the TTE screeners
    print("[DEBUG] Initializing Browser...", flush=True)
    browser = Browser(
        keep_open=True,
        screener_shorttitle="",  # Not used in tiered mode
        screener_name="",
        drawer_shorttitle="",
        drawer_name="",
        interval_minutes=10,
        start_fresh=False,
        screener_ob_short=NWE_SCREENER_SHORTTITLE,  # Use TTE NWE Screener
        screener_ob_name=NWE_SCREENER_NAME,
        screener_nw_short=OBDIV_SCREENER_SHORTTITLE,  # Use TTE OBDIV Screener
        screener_nw_name=OBDIV_SCREENER_NAME,
        screener_sb_short="",  # Not used
        screener_sb_name="",
    )
    print("[DEBUG] Browser initialized", flush=True)

    # Sign in to TradingView
    print("[DEBUG] Calling browser.sign_in()...", flush=True)
    logger.info("Signing in to TradingView...")
    if not browser.sign_in():
        raise RuntimeError("Failed to sign in to TradingView")
    print("[DEBUG] sign_in() returned True", flush=True)

    # Navigate to NWE chart URL
    print(f"[DEBUG] Navigating to NWE chart: {config.nwe_chart_url}", flush=True)
    logger.info(f"Navigating to NWE chart: {config.nwe_chart_url}")
    if not browser.open_page(config.nwe_chart_url):
        raise RuntimeError(f"Failed to open NWE chart URL: {config.nwe_chart_url}")
    print("[DEBUG] NWE chart page opened", flush=True)

    # Wait for page to fully load
    import time

    print("[DEBUG] Waiting 5s for page to load...", flush=True)
    time.sleep(5)
    print("[DEBUG] Wait complete", flush=True)

    # Open alerts sidebar
    print("[DEBUG] Opening alerts sidebar...", flush=True)
    logger.info("Opening alerts sidebar...")
    browser.open_alerts_sidebar()
    print("[DEBUG] Alerts sidebar opened", flush=True)

    # Delete any existing alerts
    print("[DEBUG] Deleting existing alerts...", flush=True)
    logger.info("Deleting existing alerts...")
    browser.delete_all_alerts()
    print("[DEBUG] Alerts deleted", flush=True)

    print("[DEBUG] create_orchestrator() complete - returning orchestrator", flush=True)
    return TieredOrchestrator(browser, api_client, config)
