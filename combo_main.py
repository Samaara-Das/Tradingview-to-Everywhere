"""
TTE Combo Mode — Entry Point

Creates persistent webhook alerts on TradingView (3 symbols each, ~1054 total),
then runs maintenance every 5 minutes to restart inactive alerts.

Usage:
    python combo_main.py                  # Full setup + maintenance
    python combo_main.py --setup-only     # Create alerts, then exit
    python combo_main.py --maintain-only  # Skip setup, run maintenance only
    python combo_main.py --fresh          # Delete all existing alerts before setup
    python combo_main.py --validate       # Validate config and exit
"""

import os
import argparse
import signal
import sys
from time import sleep, time

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
if hasattr(signal, "SIGBREAK"):
    signal.signal(signal.SIGBREAK, _signal_handler)


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
# Browser setup
# ---------------------------------------------------------------------------


def create_browser(config: ComboConfig, args) -> Browser:
    """Create and initialize a single Browser instance."""
    logger.info("Initializing browser...")

    start_fresh = getattr(args, "fresh", False)
    if start_fresh:
        logger.info("Will delete all existing alerts before setup (--fresh)")

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
        headless=config.headless,
    )

    if not browser.init_succeeded:
        raise Exception("Browser initialization failed")

    if not browser.setup_tv():
        raise Exception("TradingView setup failed")

    logger.info("Browser ready")
    return browser


# ---------------------------------------------------------------------------
# Alert creation
# ---------------------------------------------------------------------------


def run_alert_creation(
    browser: Browser,
    batches: list[list[str]],
    config: ComboConfig,
) -> dict:
    """Create alerts for all batches sequentially."""
    completed = 0
    failed = []
    batch_times = []
    creation_start = time()

    try:
        for i, batch in enumerate(batches):
            if _shutdown_requested:
                logger.info("Shutdown requested — stopping")
                break

            batch_start = time()
            logger.info(f"Batch {i+1}/{len(batches)}: {batch}")

            # Change chart symbol to match batch
            t0 = time()
            symbol_change_result = browser.open_chart.change_symbol(batch[0])
            t_symbol = time() - t0

            if not symbol_change_result:
                logger.error(f"Failed to change chart symbol to {batch[0]}")
                failed.append(
                    {
                        "batch": i,
                        "symbols": batch,
                        "error": "chart_symbol_change_failed",
                    }
                )
                continue

            # Change settings
            t0 = time()
            if not browser.change_settings(batch, config.screener_shorttitle):
                logger.error("Failed to change settings")
                failed.append(
                    {"batch": i, "symbols": batch, "error": "change_settings_failed"}
                )
                continue
            t_settings = time() - t0

            t0 = time()
            sleep(config.recalc_wait)  # Wait for screener recalculation
            t_recalc = time() - t0

            # Check for screener errors
            t0 = time()
            if not browser.is_no_error(config.screener_shorttitle):
                logger.warning("Screener has errors, attempting recovery")

                # Recovery attempt
                indicator_for_reupload = browser._safe_indicator_access(
                    config.screener_shorttitle
                )
                if not indicator_for_reupload or not browser.reupload_indicator(
                    indicator_for_reupload,
                    config.screener_name,
                    config.screener_shorttitle,
                ):
                    logger.error("Failed to re-upload screener")
                    failed.append(
                        {"batch": i, "symbols": batch, "error": "reupload_failed"}
                    )
                    continue

                sleep(config.recalc_wait)  # Wait for indicator to fully load

                # Reapply settings
                if not browser.change_settings(batch, config.screener_shorttitle):
                    logger.error("Failed to reapply settings after recovery")
                    failed.append(
                        {
                            "batch": i,
                            "symbols": batch,
                            "error": "recovery_settings_failed",
                        }
                    )
                    continue

                sleep(config.recalc_wait)  # Wait for recalculation

                # Recheck errors
                if not browser.is_no_error(config.screener_shorttitle):
                    logger.error("Screener still has errors after recovery")
                    failed.append(
                        {
                            "batch": i,
                            "symbols": batch,
                            "error": "persistent_screener_error",
                        }
                    )
                    continue

            t_error_check = time() - t0

            # Click indicator (is_no_error already validated it exists; get a fresh reference)
            try:
                indicators = browser.driver.find_elements(
                    By.CSS_SELECTOR, 'div[data-qa-id="legend-source-item"]'
                )
                indicator = None
                for ind in indicators:
                    name = ind.find_element(
                        By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]'
                    ).text
                    if name == config.screener_shorttitle:
                        indicator = ind
                        break
            except Exception:
                indicator = None

            if not indicator:
                logger.error("Indicator access failed")
                failed.append(
                    {"batch": i, "symbols": batch, "error": "indicator_access_failed"}
                )
                continue

            indicator.click()

            # Create alert
            t0 = time()
            success, error = browser.create_webhook_alert(
                config.screener_shorttitle, config.webhook_url
            )
            t_alert = time() - t0

            if success:
                completed += 1
                t_batch = time() - batch_start
                batch_times.append(t_batch)
                logger.info(
                    f"Alert created for {batch} "
                    f"[sym={t_symbol:.1f}s set={t_settings:.1f}s recalc={t_recalc:.1f}s "
                    f"err={t_error_check:.1f}s alert={t_alert:.1f}s total={t_batch:.1f}s]"
                )
            else:
                # Retry with recovery
                logger.warning("First attempt failed, retrying with recovery...")

                retry_indicator = browser._safe_indicator_access(
                    config.screener_shorttitle
                )
                if retry_indicator and browser.reupload_indicator(
                    retry_indicator, config.screener_name, config.screener_shorttitle
                ):
                    sleep(config.recalc_wait)

                    if browser.change_settings(batch, config.screener_shorttitle):
                        sleep(config.recalc_wait)

                        indicator = browser._safe_indicator_access(
                            config.screener_shorttitle
                        )
                        if indicator:
                            indicator.click()

                            success, error = browser.create_webhook_alert(
                                config.screener_shorttitle, config.webhook_url
                            )

                            if success:
                                completed += 1
                                logger.info(f"Retry succeeded for {batch}")
                            else:
                                failed.append(
                                    {
                                        "batch": i,
                                        "symbols": batch,
                                        "error": f"retry_{error}",
                                    }
                                )
                                logger.warning(f"Retry failed — {error}")
                        else:
                            failed.append(
                                {
                                    "batch": i,
                                    "symbols": batch,
                                    "error": "retry_indicator_access_failed",
                                }
                            )
                            logger.error("Retry failed - indicator access failed")
                    else:
                        failed.append(
                            {
                                "batch": i,
                                "symbols": batch,
                                "error": "retry_settings_failed",
                            }
                        )
                        logger.error("Retry failed - settings reapplication failed")
                else:
                    failed.append(
                        {"batch": i, "symbols": batch, "error": "retry_reupload_failed"}
                    )
                    logger.error("Retry failed - re-upload failed")

            sleep(config.alert_creation_delay)

    except Exception as e:
        logger.exception("Fatal error during alert creation")
        return {
            "completed": 0,
            "failed": [],
            "total": len(batches),
            "error": str(e),
        }

    # Log timing summary
    total_elapsed = time() - creation_start
    if batch_times:
        avg_batch = sum(batch_times) / len(batch_times)
        logger.info(
            f"Timing summary — "
            f"{len(batch_times)} batches in {total_elapsed:.0f}s, "
            f"avg {avg_batch:.1f}s/batch"
        )

    return {
        "completed": completed,
        "failed": failed,
        "total": len(batches),
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
        print(f"  Headless: {config.headless}", flush=True)
        print(f"  Screener: {config.screener_shorttitle}", flush=True)
        print(f"  Webhook URL: {config.webhook_url}", flush=True)
        print(f"  Batch size: {config.batch_size}", flush=True)
        print(f"  Creation delay: {config.alert_creation_delay}s", flush=True)
        print(f"  Recalc wait: {config.recalc_wait}s", flush=True)
        print(f"  Maintenance interval: {config.maintenance_interval}s", flush=True)
        sys.exit(0)

    # --- Maintain only mode ---
    if args.maintain_only:
        logger.info("Running maintenance only (--maintain-only)")
        browser = create_browser(config, args)
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

    # --- Initialize browser ---
    browser = create_browser(config, args)

    # --- Run alert creation ---
    logger.info("Starting alert creation...")
    result = run_alert_creation(browser, batches, config)

    logger.info(f"Finished: {result['completed']}/{result['total']} alerts created")
    if result["failed"]:
        logger.warning(f"{len(result['failed'])} batches failed:")
        for fb in result["failed"]:
            logger.warning(f"  Batch {fb['batch']}: {fb['symbols']} — {fb['error']}")

    # --- Setup only mode ---
    if args.setup_only:
        logger.info("Setup complete (--setup-only). Exiting.")
        try:
            browser.driver.quit()
        except Exception:
            pass
        return

    # --- Maintenance loop (reuse the same browser) ---
    logger.info("Starting maintenance mode...")

    try:
        run_maintenance(browser, config.maintenance_interval)
    finally:
        try:
            browser.driver.quit()
            logger.info("Browser closed successfully")
        except Exception:
            pass


if __name__ == "__main__":
    main()
