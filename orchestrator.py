"""
Main Orchestration Logic for TTE Tiered Screener System.

Manages the workflow:
1. NWE Symbol Batch Rotation - Cycle through 1000+ symbols
2. OBDIV Hot Symbol Processing - Process triggered symbols through Tier 2
3. Screenshot Capture - Capture charts for completed signals
"""

import time
import signal
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import Config
from api_client import StockBuddyAPIClient, APIError
from selenium_manager import SeleniumManager, SeleniumError
from utils.logger import get_logger

logger = get_logger('orchestrator')


class OrchestratorError(Exception):
    """Raised when orchestration encounters a critical error."""
    pass


class TieredOrchestrator:
    """
    Orchestrates the tiered screening workflow.

    Manages three phases in each cycle:
    1. NWE Batch Rotation - Updates NWE screener with next batch of symbols
    2. OBDIV Processing - Processes hot symbols through Tier 2 screener
    3. Screenshot Capture - Captures charts for signals needing screenshots

    Attributes:
        api: Stock Buddy API client
        browser: Selenium browser manager
        running: Whether the orchestrator is running
        stats: Runtime statistics
    """

    def __init__(self):
        """Initialize the orchestrator."""
        self.api = StockBuddyAPIClient()
        self.browser: Optional[SeleniumManager] = None
        self.running = False

        # Runtime statistics
        self.stats = {
            'cycles_completed': 0,
            'nwe_batches_processed': 0,
            'obdiv_symbols_processed': 0,
            'screenshots_captured': 0,
            'errors': 0,
            'started_at': None
        }

        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False

    def _get_browser(self) -> SeleniumManager:
        """
        Get or create browser manager.

        Returns:
            SeleniumManager instance
        """
        if self.browser is None:
            self.browser = SeleniumManager()
        return self.browser

    def _log_stats(self):
        """Log current runtime statistics."""
        if self.stats['started_at']:
            runtime = datetime.now() - self.stats['started_at']
            runtime_str = str(runtime).split('.')[0]  # Remove microseconds
        else:
            runtime_str = "N/A"

        logger.info(
            f"Stats: Cycles={self.stats['cycles_completed']}, "
            f"NWE={self.stats['nwe_batches_processed']}, "
            f"OBDIV={self.stats['obdiv_symbols_processed']}, "
            f"Screenshots={self.stats['screenshots_captured']}, "
            f"Errors={self.stats['errors']}, "
            f"Runtime={runtime_str}"
        )

    def start(self):
        """
        Start the orchestration loop.

        Runs continuously until stopped via signal or stop() method.
        """
        logger.info("=" * 60)
        logger.info("TTE Tiered Orchestrator Starting")
        logger.info("=" * 60)

        # Verify API connectivity
        logger.info("Checking API connectivity...")
        if not self.api.health_check():
            logger.error("Cannot connect to Stock Buddy API. Exiting.")
            raise OrchestratorError("API connection failed")

        logger.info("API health check passed")

        # Log initial system stats
        try:
            api_stats = self.api.get_stats()
            rotation = api_stats.get('rotation', {})
            signals = api_stats.get('signals', {})

            logger.info(
                f"System state: Batch #{rotation.get('batch_number', 0)}, "
                f"Rotation #{rotation.get('rotation_number', 0)}, "
                f"Total signals: {signals.get('total', 0)}"
            )
        except Exception as e:
            logger.warning(f"Could not fetch initial stats: {e}")

        # Log configuration
        logger.info(
            f"Config: NWE batch={Config.NWE_BATCH_SIZE}, "
            f"OBDIV batch={Config.OBDIV_BATCH_SIZE}, "
            f"NWE wait={Config.NWE_BATCH_WAIT}s, "
            f"OBDIV wait={Config.OBDIV_BATCH_WAIT}s"
        )

        self.running = True
        self.stats['started_at'] = datetime.now()

        while self.running:
            try:
                cycle_start = time.time()
                logger.info("-" * 60)
                logger.info(f"Starting cycle #{self.stats['cycles_completed'] + 1}")

                # Phase 1: NWE Symbol Batch Rotation
                self._process_nwe_batch()

                if not self.running:
                    break

                # Phase 2: OBDIV Hot Symbol Processing
                self._process_obdiv_batch()

                if not self.running:
                    break

                # Phase 3: Screenshot Capture
                self._capture_pending_screenshots()

                # Cycle complete
                cycle_duration = time.time() - cycle_start
                self.stats['cycles_completed'] += 1

                logger.info(f"Cycle completed in {cycle_duration:.1f}s")
                self._log_stats()

                # Brief pause between cycles
                if self.running:
                    time.sleep(Config.POLL_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Shutdown requested by user (Ctrl+C)")
                break

            except OrchestratorError as e:
                logger.error(f"Critical orchestration error: {e}")
                self.stats['errors'] += 1
                raise

            except Exception as e:
                logger.exception(f"Unexpected error in orchestration cycle: {e}")
                self.stats['errors'] += 1

                # Back off on errors, but continue
                if self.running:
                    logger.info("Backing off for 30s before retry...")
                    time.sleep(30)

        self.stop()

    def stop(self):
        """Stop the orchestrator gracefully."""
        logger.info("Stopping orchestrator...")
        self.running = False

        # Close browser
        if self.browser:
            try:
                self.browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self.browser = None

        # Close API client
        try:
            self.api.close()
        except Exception as e:
            logger.warning(f"Error closing API client: {e}")

        # Log final stats
        self._log_stats()
        logger.info("Orchestrator stopped")

    def _process_nwe_batch(self):
        """
        Fetch and process next batch of symbols through NWE screener.

        Updates the NWE screener indicator with the next batch of symbols
        and waits for it to process.
        """
        logger.info("Phase 1: NWE Batch Rotation")

        try:
            # Get next batch from API
            batch_response = self.api.get_next_symbol_batch(size=Config.NWE_BATCH_SIZE)

            if not batch_response.get('success'):
                logger.warning("Failed to get symbol batch from API")
                return

            symbols_data = batch_response.get('batch', [])

            if not symbols_data:
                logger.info("No symbols in batch - may need to wait for rotation reset")
                time.sleep(30)
                return

            # Extract symbol names
            symbols = [s['symbol'] for s in symbols_data]
            rotation = batch_response.get('rotation', {})
            batch_num = rotation.get('batch_number', '?')
            rotation_num = rotation.get('rotation_number', '?')
            total = rotation.get('total_symbols', '?')
            scanned = rotation.get('symbols_scanned_this_rotation', 0)

            logger.info(
                f"Batch #{batch_num} (Rotation #{rotation_num}): "
                f"{len(symbols)} symbols ({scanned}/{total})"
            )
            logger.debug(f"Symbols: {', '.join(symbols)}")

            # Update NWE screener via Selenium
            try:
                browser = self._get_browser()
                browser.update_nwe_symbols(symbols)

                # Wait for NWE screener to process
                logger.info(f"Waiting {Config.NWE_BATCH_WAIT}s for NWE scan...")
                time.sleep(Config.NWE_BATCH_WAIT)

            except SeleniumError as e:
                logger.error(f"Selenium error updating NWE screener: {e}")
                # Continue to mark as scanned even if Selenium fails
                # (symbols may have been processed via webhooks)

            # Mark symbols as scanned
            self.api.mark_symbols_scanned(symbols)
            self.stats['nwe_batches_processed'] += 1

            logger.info(f"Batch #{batch_num} complete")

        except APIError as e:
            logger.error(f"API error in NWE batch: {e}")
            self.stats['errors'] += 1

        except Exception as e:
            logger.exception(f"Unexpected error in NWE batch: {e}")
            self.stats['errors'] += 1

    def _process_obdiv_batch(self):
        """
        Process hot symbols through OBDIV (Tier 2) screener.

        Gets symbols from hot list and updates OBDIV screener to process them.
        """
        logger.info("Phase 2: OBDIV Processing")

        try:
            # Get hot symbols awaiting Tier 2
            hot_symbols = self.api.get_hot_symbols(limit=Config.OBDIV_BATCH_SIZE)

            if not hot_symbols:
                logger.info("No hot symbols pending OBDIV check")
                return

            symbols = [s['symbol'] for s in hot_symbols]
            logger.info(f"Processing {len(symbols)} hot symbols: {', '.join(symbols)}")

            # Update OBDIV screener via Selenium
            try:
                browser = self._get_browser()
                browser.update_obdiv_symbols(symbols)

                # Wait for OBDIV screener to process
                logger.info(f"Waiting {Config.OBDIV_BATCH_WAIT}s for OBDIV scan...")
                time.sleep(Config.OBDIV_BATCH_WAIT)

                self.stats['obdiv_symbols_processed'] += len(symbols)

            except SeleniumError as e:
                logger.error(f"Selenium error updating OBDIV screener: {e}")
                self.stats['errors'] += 1

            logger.info("OBDIV processing complete")

        except APIError as e:
            logger.error(f"API error in OBDIV processing: {e}")
            self.stats['errors'] += 1

        except Exception as e:
            logger.exception(f"Unexpected error in OBDIV processing: {e}")
            self.stats['errors'] += 1

    def _capture_pending_screenshots(self):
        """
        Capture screenshots for signals that need them.

        Iterates through signals with pending_screenshot status and
        captures chart screenshots.
        """
        logger.info("Phase 3: Screenshot Capture")

        try:
            # Get signals needing screenshots
            pending = self.api.get_pending_screenshots(limit=Config.SCREENSHOT_BATCH_SIZE)

            if not pending:
                logger.info("No signals pending screenshots")
                return

            logger.info(f"Capturing screenshots for {len(pending)} signals")

            browser = self._get_browser()

            for signal in pending:
                if not self.running:
                    break

                try:
                    # MongoDB uses _id, but API might return id or _id
                    signal_id = signal.get('_id') or signal.get('id')
                    symbol = signal.get('symbol')
                    
                    if not signal_id:
                        logger.warning(f"Signal missing ID: {signal}")
                        continue

                    # Determine best timeframe for screenshot
                    # Prefer OB timeframe, fall back to first NWE timeframe
                    ob_tf = signal.get('ob_tf')
                    nwe_tf = signal.get('nwe_tf', ['H4'])

                    if ob_tf:
                        timeframe = ob_tf
                    elif isinstance(nwe_tf, list) and nwe_tf:
                        timeframe = nwe_tf[0]
                    else:
                        timeframe = 'H4'

                    # Map timeframe to TradingView format
                    tf_map = {
                        'H1': '60',
                        'H4': '240',
                        'D1': 'D',
                        'D': 'D',
                        'W1': 'W',
                        'W': 'W',
                        'M1': 'M'
                    }
                    tv_timeframe = tf_map.get(timeframe, timeframe)

                    logger.info(f"Capturing screenshot: {symbol} on {timeframe}")

                    # Capture screenshot
                    screenshot_url = browser.capture_chart_screenshot(symbol, tv_timeframe)

                    # Update signal with screenshot URL
                    self.api.update_signal_screenshot(signal_id, screenshot_url)
                    self.stats['screenshots_captured'] += 1

                    logger.info(f"Screenshot complete for signal {signal_id}")

                except SeleniumError as e:
                    logger.error(f"Screenshot capture failed for {signal.get('symbol')}: {e}")
                    self.stats['errors'] += 1

                except APIError as e:
                    logger.error(f"API error updating screenshot for {signal.get('symbol')}: {e}")
                    self.stats['errors'] += 1

                except Exception as e:
                    logger.exception(f"Unexpected error capturing screenshot: {e}")
                    self.stats['errors'] += 1

        except APIError as e:
            logger.error(f"API error getting pending screenshots: {e}")
            self.stats['errors'] += 1

        except Exception as e:
            logger.exception(f"Unexpected error in screenshot phase: {e}")
            self.stats['errors'] += 1


def main():
    """Entry point for running the orchestrator directly."""
    orchestrator = TieredOrchestrator()

    try:
        orchestrator.start()
    except OrchestratorError as e:
        logger.error(f"Orchestrator failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        orchestrator.stop()


if __name__ == "__main__":
    main()
