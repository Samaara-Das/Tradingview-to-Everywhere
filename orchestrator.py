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
                self._phase2_obdiv_processing()

                logger.info(f"=== Completed cycle #{cycle_count} ===")

                if single_cycle:
                    logger.info("Single cycle mode - stopping orchestrator")
                    break

                # Wait before next cycle
                if self.config.cycle_interval > 0:
                    logger.info(
                        f"Waiting {self.config.cycle_interval}s before next cycle..."
                    )
                    time.sleep(self.config.cycle_interval)

            except Exception as e:
                logger.exception(f"Error in cycle #{cycle_count}: {e}")
                # Continue to next cycle after a delay
                time.sleep(self.config.retry_delay)

    def stop(self):
        """Stop the orchestrator gracefully."""
        logger.info("Stopping orchestrator...")
        self.running = False

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
            # Ensure we're on the NWE layout
            if not self.browser.change_layout(NWE_LAYOUT_NAME):
                logger.warning("Could not switch to NWE layout, attempting anyway...")

            # Input symbols into the NWE screener
            if not self._input_symbols_to_screener(
                symbol_strings, NWE_SCREENER_SHORTTITLE
            ):
                logger.error("Failed to input symbols into NWE screener")
                return

            # Give the screener time to recalculate
            time.sleep(3)

            # Create webhook alert for NWE screener
            if not self.browser.create_webhook_alert(
                NWE_SCREENER_SHORTTITLE, self.nwe_webhook_url
            ):
                logger.error("Failed to create webhook alert for NWE screener")
                return

            logger.info(
                f"Waiting {self.config.nwe_batch_wait}s for NWE webhook to fire..."
            )
            time.sleep(self.config.nwe_batch_wait)

            # Delete the alert
            if not self.browser.delete_all_alerts():
                logger.warning("Failed to delete alerts, continuing anyway...")

            # Mark symbols as scanned
            mark_response = self.api.mark_symbols_scanned(symbol_strings)
            if mark_response.get("success", False):
                logger.info(f"Marked {len(symbol_strings)} symbols as scanned")
            else:
                logger.warning(
                    f"Failed to mark symbols as scanned: {mark_response.get('error', 'Unknown error')}"
                )

        except Exception as e:
            logger.exception(f"Error in Phase 1: {e}")
            # Try to clean up alerts
            try:
                self.browser.delete_all_alerts()
            except:
                pass

    def _phase2_obdiv_processing(self):
        """
        Phase 2: OBDIV Processing

        1. Fetch hot symbols from API
        2. Switch to OBDIV layout
        3. Process hot symbols in batches
        4. Switch back to NWE layout
        """
        logger.info("--- Phase 2: OBDIV Processing ---")

        # Get hot symbols pending Tier 2 processing
        hot_symbols = self.api.get_hot_symbols(limit=50)  # Get more, we'll batch them

        if not hot_symbols:
            logger.info("No hot symbols to process - skipping OBDIV phase")
            return

        logger.info(f"Found {len(hot_symbols)} hot symbols for OBDIV processing")

        try:
            # Switch to OBDIV layout
            if not self.browser.change_layout(OBDIV_LAYOUT_NAME):
                logger.error("Could not switch to OBDIV layout")
                return

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

                # Create webhook alert for OBDIV screener
                if not self.browser.create_webhook_alert(
                    OBDIV_SCREENER_SHORTTITLE, self.obdiv_webhook_url
                ):
                    logger.error("Failed to create webhook alert for OBDIV screener")
                    continue

                logger.info(
                    f"Waiting {self.config.obdiv_batch_wait}s for OBDIV webhook to fire..."
                )
                time.sleep(self.config.obdiv_batch_wait)

                # Delete the alert
                if not self.browser.delete_all_alerts():
                    logger.warning("Failed to delete alerts, continuing anyway...")

                processed_count += len(symbol_strings)

            logger.info(f"Completed OBDIV processing for {processed_count} symbols")

        except Exception as e:
            logger.exception(f"Error in Phase 2: {e}")
            # Try to clean up alerts
            try:
                self.browser.delete_all_alerts()
            except:
                pass
        finally:
            # Always try to switch back to NWE layout
            try:
                self.browser.change_layout(NWE_LAYOUT_NAME)
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
