"""
TTE Combo Mode — Entry Point

Creates 264 persistent webhook alerts on TradingView (4 symbols each, ~1054 total),
using parallel browser instances to reduce setup time, then runs maintenance every 5 minutes
to restart inactive alerts.

Usage:
    python combo_main.py                  # Full setup + maintenance
    python combo_main.py --setup-only     # Create alerts, then exit
    python combo_main.py --maintain-only  # Skip setup, run maintenance only
    python combo_main.py --fresh          # Delete all existing alerts before setup
    python combo_main.py --validate       # Validate config and exit
"""

# Prevent MongoDB auto-loading at import time (combo loads symbols on demand)
import os

os.environ["SKIP_MONGODB_SYMBOLS"] = "true"

import argparse
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

import logger_setup
from combo_config import ComboConfig
from open_tv import Browser
from resources.utils import Utils

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Logger
logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

# Graceful shutdown flag
_shutdown_requested = False


def _signal_handler(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    logger.info("Shutdown requested — will exit after current operations complete")


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ---------------------------------------------------------------------------
# Symbol fetching
# ---------------------------------------------------------------------------


def fetch_all_symbols() -> list[str]:
    """Fetch all symbols from MongoDB and return as a flat list.

    Uses symbol_settings.get_symbols() which returns {category: [symbols...]}.
    """
    from resources.symbol_settings import get_symbols

    logger.info("Fetching symbols from MongoDB...")
    symbols_by_category = get_symbols()

    all_symbols = []
    for category, symbols in symbols_by_category.items():
        logger.info(f"  {category}: {len(symbols)} symbols")
        all_symbols.extend(symbols)

    logger.info(f"Total symbols fetched: {len(all_symbols)}")
    return all_symbols


def chunk_symbols(symbols: list[str], size: int = 3) -> list[list[str]]:
    """Split symbols into batches of `size`."""
    return [symbols[i : i + size] for i in range(0, len(symbols), size)]


# ---------------------------------------------------------------------------
# Multi-browser architecture
# ---------------------------------------------------------------------------


def assign_batches_to_browsers(batches: list, num_browsers: int) -> list[list]:
    """Pre-divide batches into equal non-overlapping ranges.

    Example with 258 batches, 3 browsers:
      Browser 0: batches[0:86]    (86 batches)
      Browser 1: batches[86:172]  (86 batches)
      Browser 2: batches[172:258] (86 batches)
    """
    batch_size = len(batches) // num_browsers
    remainder = len(batches) % num_browsers

    ranges = []
    start = 0
    for i in range(num_browsers):
        # Distribute remainder across first few browsers
        size = batch_size + (1 if i < remainder else 0)
        ranges.append(batches[start : start + size])
        start += size

    return ranges


def create_browser_instance(browser_id: int, config: ComboConfig, args) -> Browser:
    """Create a Browser instance with unique Chrome profile for parallel execution."""
    logger.info(f"Browser {browser_id}: Initializing...")

    # Only delete alerts on the first browser to avoid race conditions
    # Subsequent browsers will see alerts already deleted
    start_fresh = True if browser_id == 0 else False

    if start_fresh:
        logger.info("Browser 0: Will delete all existing alerts before setup")

    # Use same profile but different user data dir suffix for each browser
    # This allows parallel execution without profile conflicts
    chrome_profile = "Profile 4"  # All browsers use Profile 4
    user_data_suffix = f"_browser{browser_id}" if browser_id > 0 else ""
    logger.info(
        f"Browser {browser_id}: Using Chrome profile '{chrome_profile}' with suffix '{user_data_suffix}'"
    )

    # Session copying happens earlier in main() before any browser launches

    browser = Browser(
        keep_open=True,
        screener_shorttitle=config.screener_shorttitle,
        screener_name=config.screener_name,
        drawer_shorttitle="",
        drawer_name="",
        interval_minutes=config.maintenance_interval // 60,
        start_fresh=start_fresh,
        screener_ob_short=config.screener_shorttitle,
        screener_ob_name=config.screener_name,
        screener_nw_short=config.screener_shorttitle,
        screener_nw_name=config.screener_name,
        screener_sb_short=config.screener_shorttitle,
        screener_sb_name=config.screener_name,
        mode="combo",
        layout_name=config.layout_name,
        chart_timeframe=config.chart_timeframe,
        bar_style=config.bar_style,
        chrome_profile=chrome_profile,
        user_data_suffix=user_data_suffix,
        browser_id=browser_id,
    )

    if not browser.init_succeeded:
        raise Exception(f"Browser {browser_id}: Initialization failed")

    if not browser.setup_tv():
        raise Exception(f"Browser {browser_id}: TradingView setup failed")

    logger.info(f"Browser {browser_id}: Ready")
    return browser


def run_alert_creation(
    browser_id: int,
    browser: Browser,
    assigned_batches: list[list[str]],
    config: ComboConfig,
) -> dict:
    """Create alerts for assigned batches using an already-initialized browser.

    This runs in its own thread for parallel alert creation.
    """
    completed = 0
    failed = []

    try:
        for i, batch in enumerate(assigned_batches):
            if _shutdown_requested:
                logger.info(f"Browser {browser_id}: Shutdown requested — stopping")
                break

            logger.info(
                f"Browser {browser_id}: Batch {i+1}/{len(assigned_batches)}: {batch}"
            )

            # Change chart symbol to match batch
            logger.info(
                f"[DEBUG] Browser {browser_id}: BEFORE symbol change - attempting to change to {batch[0]}"
            )
            symbol_change_result = browser.open_chart.change_symbol(batch[0])
            logger.info(
                f"[DEBUG] Browser {browser_id}: AFTER symbol change - result={symbol_change_result}, target={batch[0]}"
            )

            if not symbol_change_result:
                logger.error(
                    f"Browser {browser_id}: Failed to change chart symbol to {batch[0]}"
                )
                failed.append(
                    {
                        "batch": i,
                        "symbols": batch,
                        "error": "chart_symbol_change_failed",
                    }
                )
                continue

            # Change settings
            if not browser.change_settings(batch, config.screener_shorttitle):
                logger.error(f"Browser {browser_id}: Failed to change settings")
                failed.append(
                    {"batch": i, "symbols": batch, "error": "change_settings_failed"}
                )
                continue

            sleep(3)  # Wait for screener recalculation

            # Check for screener errors
            if not browser.is_no_error(config.screener_shorttitle):
                logger.warning(
                    f"Browser {browser_id}: Screener has errors, attempting recovery"
                )

                # Recovery attempt
                # Get fresh indicator reference for reupload
                indicator_for_reupload = browser._safe_indicator_access(
                    config.screener_shorttitle
                )
                if not indicator_for_reupload or not browser.reupload_indicator(
                    indicator_for_reupload,
                    config.screener_name,
                    config.screener_shorttitle,
                ):
                    logger.error(f"Browser {browser_id}: Failed to re-upload screener")
                    failed.append(
                        {"batch": i, "symbols": batch, "error": "reupload_failed"}
                    )
                    continue

                # Reinitialize reference
                sleep(2)  # Wait for indicator to fully load

                # Reapply settings
                if not browser.change_settings(batch, config.screener_shorttitle):
                    logger.error(
                        f"Browser {browser_id}: Failed to reapply settings after recovery"
                    )
                    failed.append(
                        {
                            "batch": i,
                            "symbols": batch,
                            "error": "recovery_settings_failed",
                        }
                    )
                    continue

                sleep(3)  # Wait for recalculation

                # Recheck errors
                if not browser.is_no_error(config.screener_shorttitle):
                    logger.error(
                        f"Browser {browser_id}: Screener still has errors after recovery"
                    )
                    failed.append(
                        {
                            "batch": i,
                            "symbols": batch,
                            "error": "persistent_screener_error",
                        }
                    )
                    continue

            # Click indicator
            indicator = browser._safe_indicator_access(config.screener_shorttitle)
            if not indicator:
                logger.error(f"Browser {browser_id}: Indicator access failed")
                failed.append(
                    {"batch": i, "symbols": batch, "error": "indicator_access_failed"}
                )
                continue

            indicator.click()

            # Create alert
            success, error = browser.create_webhook_alert(
                config.screener_shorttitle, config.webhook_url
            )

            if success:
                completed += 1
                logger.info(f"Browser {browser_id}: Alert created for {batch}")
            else:
                # Retry with recovery
                logger.warning(
                    f"Browser {browser_id}: First attempt failed, retrying with recovery..."
                )

                # Re-upload screener
                # Get fresh indicator reference for reupload
                retry_indicator = browser._safe_indicator_access(
                    config.screener_shorttitle
                )
                if retry_indicator and browser.reupload_indicator(
                    retry_indicator, config.screener_name, config.screener_shorttitle
                ):
                    sleep(2)

                    # Reapply settings
                    if browser.change_settings(batch, config.screener_shorttitle):
                        sleep(3)

                        # Click indicator again
                        indicator = browser._safe_indicator_access(
                            config.screener_shorttitle
                        )
                        if indicator:
                            indicator.click()

                            # Retry alert creation
                            success, error = browser.create_webhook_alert(
                                config.screener_shorttitle, config.webhook_url
                            )

                            if success:
                                completed += 1
                                logger.info(
                                    f"Browser {browser_id}: Retry succeeded for {batch}"
                                )
                            else:
                                failed.append(
                                    {
                                        "batch": i,
                                        "symbols": batch,
                                        "error": f"retry_{error}",
                                    }
                                )
                                logger.warning(
                                    f"Browser {browser_id}: Retry failed — {error}"
                                )
                        else:
                            failed.append(
                                {
                                    "batch": i,
                                    "symbols": batch,
                                    "error": "retry_indicator_access_failed",
                                }
                            )
                            logger.error(
                                f"Browser {browser_id}: Retry failed - indicator access failed"
                            )
                    else:
                        failed.append(
                            {
                                "batch": i,
                                "symbols": batch,
                                "error": "retry_settings_failed",
                            }
                        )
                        logger.error(
                            f"Browser {browser_id}: Retry failed - settings reapplication failed"
                        )
                else:
                    failed.append(
                        {"batch": i, "symbols": batch, "error": "retry_reupload_failed"}
                    )
                    logger.error(
                        f"Browser {browser_id}: Retry failed - re-upload failed"
                    )

            sleep(config.alert_creation_delay)

    except Exception as e:
        logger.exception(f"Browser {browser_id}: Fatal error during alert creation")
        return {
            "browser_id": browser_id,
            "completed": 0,
            "failed": [],
            "total": len(assigned_batches),
            "error": str(e),
        }
    finally:
        # Cleanup - always quit driver, even on error or shutdown
        try:
            browser.driver.quit()
            logger.info(f"Browser {browser_id}: Driver closed successfully")
        except Exception as e:
            logger.debug(
                f"Browser {browser_id}: Error during quit (expected during shutdown): {e}"
            )

    return {
        "browser_id": browser_id,
        "completed": completed,
        "failed": failed,
        "total": len(assigned_batches),
    }


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------


def restart_inactive_alerts(driver) -> bool:
    """Restart all inactive alerts via TradingView UI.

    Standalone function (no Alerts class dependency). Replicates the Selenium
    steps from handle_alerts.py:240-303.
    """
    utils = Utils()
    try:
        # Make sure that the Alerts tab is open
        utils.open_alert_tab(driver)

        # Click the 3-dot settings button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]')
            )
        ).click()

        # Wait for the dropdown to show up
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]')
            )
        )

        # Check if the "Show Alerts" section is minimised. If so, expand it
        show_all_section = dropdown.find_element(
            By.CSS_SELECTOR, 'div[class="section-xZRtm41u summary-ynHBVe1n"]'
        )
        maximized = show_all_section.get_attribute("data-open") == "true"
        if not maximized:
            show_all_section.click()
            logger.info('Expanded the "Show Alerts" section')

        # Check if the "All" option is selected. If not, select it
        all_option = dropdown.find_element(
            By.CSS_SELECTOR, 'div[class="item-xZRtm41u item-jFqVJoPk"]'
        )
        if not all_option.find_element(By.TAG_NAME, "input").is_selected():
            all_option.click()
            logger.info('Selected the "All" option')

        # Find "Restart all inactive" button (may be disabled when no inactive alerts)
        restart_buttons = [
            el
            for el in dropdown.find_elements(
                By.CSS_SELECTOR, "div.item-jFqVJoPk.withIcon-jFqVJoPk"
            )
            if "Restart all inactive" in el.text
        ]
        if not restart_buttons:
            logger.info("No 'Restart all inactive' button found in dropdown")
        elif "isDisabled" in (restart_buttons[0].get_attribute("class") or ""):
            logger.info("No inactive alerts to restart (button is disabled)")
        else:
            restart_buttons[0].click()
            logger.info('Clicked on "Restart all inactive"')

            # Click Yes on the confirmation popup
            popup = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]')
                )
            )
            popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
            logger.info("Restarting all inactive alerts!")

        sleep(1)
        return True

    except Exception as e:
        logger.exception("Error restarting inactive alerts:")
        return False


def clear_alert_log(driver) -> bool:
    """Clear the TradingView alert log to prevent it from growing indefinitely."""
    utils = Utils()
    try:
        utils.open_log_tab(driver)

        # Click clear log button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'div[data-name="clear-log-button"]')
            )
        ).click()

        # Confirm in dialog
        popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]')
            )
        )
        popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
        logger.info("Alert log cleared!")
        sleep(1)
        return True
    except Exception:
        logger.exception("Error clearing alert log:")
        return False


def run_maintenance(browser: Browser, interval: int):
    """Loop: restart inactive alerts + clear log every `interval` seconds."""
    global _shutdown_requested

    logger.info(f"Maintenance loop started (every {interval}s)")

    while not _shutdown_requested:
        sleep(interval)
        if _shutdown_requested:
            break

        logger.info("Running maintenance cycle...")
        try:
            # Refresh page to keep session alive
            browser.driver.refresh()
            sleep(5)

            # Restart inactive alerts
            restart_inactive_alerts(browser.driver)

            # Clear alert log
            clear_alert_log(browser.driver)

        except Exception:
            logger.exception("Maintenance cycle failed, will retry next cycle:")

    logger.info("Maintenance loop stopped")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(description="TTE Combo Mode")
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Create alerts then exit (no maintenance loop)",
    )
    parser.add_argument(
        "--maintain-only",
        action="store_true",
        help="Skip alert setup, only run maintenance loop",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete all existing alerts before setup",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and exit",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = ComboConfig()

    # --- Validate ---
    errors = config.validate()
    if errors:
        for e in errors:
            print(f"[CONFIG ERROR] {e}", flush=True)
        sys.exit(1)

    if args.validate:
        print("Configuration is valid!", flush=True)
        print(f"  Layout: {config.layout_name}", flush=True)
        print(f"  Chart timeframe: {config.chart_timeframe}", flush=True)
        print(f"  Bar style: {config.bar_style}", flush=True)
        print(f"  Screener: {config.screener_shorttitle}", flush=True)
        print(f"  Webhook URL: {config.webhook_url}", flush=True)
        print(f"  Batch size: {config.batch_size}", flush=True)
        print(f"  Num browsers: {config.num_browsers}", flush=True)
        print(f"  Maintenance interval: {config.maintenance_interval}s", flush=True)
        sys.exit(0)

    # --- Maintain only mode ---
    if args.maintain_only:
        logger.info("Running maintenance only (--maintain-only)")
        # Create single browser for maintenance
        browser = create_browser_instance(0, config, args)
        run_maintenance(browser, config.maintenance_interval)
        return

    # --- Fetch symbols and create batches ---
    all_symbols = fetch_all_symbols()
    if not all_symbols:
        logger.error("No symbols fetched — cannot continue")
        sys.exit(1)

    logger.info(f"Total symbols for alert creation: {len(all_symbols)}")

    batches = chunk_symbols(all_symbols, config.batch_size)
    logger.info(f"Created {len(batches)} batches of {config.batch_size} symbols")

    # --- Divide batches across browsers ---
    batch_ranges = assign_batches_to_browsers(batches, config.num_browsers)

    for i, br in enumerate(batch_ranges):
        if br:
            first_idx = batches.index(br[0])
            last_idx = batches.index(br[-1])
            logger.info(
                f"Browser {i}: assigned {len(br)} batches (indices {first_idx}-{last_idx})"
            )

    # --- Initialize browsers sequentially (avoid race conditions) ---
    logger.info(f"Initializing {config.num_browsers} browsers sequentially...")
    browsers = []

    for browser_id in range(config.num_browsers):
        try:
            browser = create_browser_instance(browser_id, config, args)
            browsers.append(browser)
            logger.info(f"Browser {browser_id}: Initialized successfully")
            sleep(2)  # Small delay between browser startups to avoid conflicts
        except Exception as e:
            logger.error(f"Browser {browser_id}: Initialization failed - {e}")
            # Continue with remaining browsers
            browsers.append(None)

    # Filter out failed browsers
    active_browsers = [
        (i, b, batch_ranges[i]) for i, b in enumerate(browsers) if b is not None
    ]

    if not active_browsers:
        logger.error("All browsers failed to initialize")
        sys.exit(1)

    logger.info(f"{len(active_browsers)}/{config.num_browsers} browsers ready")

    # --- Run alert creation in parallel ---
    logger.info("Starting parallel alert creation...")

    # Create executor explicitly for proper shutdown handling
    executor = ThreadPoolExecutor(max_workers=len(active_browsers))
    results = []

    try:
        futures = []

        for browser_id, browser, batches in active_browsers:
            future = executor.submit(
                run_alert_creation,
                browser_id,
                browser,
                batches,
                config,
            )
            futures.append(future)

        # Collect results
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                logger.info(
                    f"Browser {result['browser_id']} finished: {result['completed']}/{result['total']} succeeded"
                )
            except Exception as e:
                logger.error(f"Future execution failed: {e}")
    finally:
        # Graceful executor shutdown: wait for running tasks, don't cancel futures
        executor.shutdown(wait=True, cancel_futures=False)
        logger.info("ThreadPoolExecutor shutdown complete")

    # --- Aggregate stats ---
    total_completed = sum(r["completed"] for r in results)
    total_batches = sum(r["total"] for r in results)
    total_failed = sum(len(r["failed"]) for r in results)

    logger.info(
        f"All browsers finished: {total_completed}/{total_batches} total alerts created"
    )
    if total_failed > 0:
        logger.warning(f"{total_failed} batches failed across all browsers")
        for r in results:
            if r["failed"]:
                logger.warning(f"Browser {r['browser_id']} failures:")
                for fb in r["failed"]:
                    logger.warning(
                        f"  Batch {fb['batch']}: {fb['symbols']} — {fb['error']}"
                    )

    # --- Setup only mode ---
    if args.setup_only:
        logger.info("Setup complete (--setup-only). Exiting.")
        return

    # --- Maintenance loop ---
    logger.info("Starting maintenance mode...")
    maintenance_browser = create_browser_instance(0, config, args)

    try:
        run_maintenance(maintenance_browser, config.maintenance_interval)
    finally:
        # Cleanup maintenance browser
        try:
            maintenance_browser.driver.quit()
            logger.info("Maintenance browser: Driver closed successfully")
        except Exception as e:
            logger.debug(
                f"Maintenance browser: Error during quit (expected during shutdown): {e}"
            )


if __name__ == "__main__":
    main()
