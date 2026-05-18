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

import argparse
import os
import platform
import signal
import subprocess
import sys
import threading
from time import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tte import log
from tte.browser.helpers import Utils
from tte.browser.tradingview import Browser
from tte.config import ComboConfig

# Logger
logger = log.setup_logger(__name__, log.INFO)

# Graceful shutdown event — allows interruptible waits via .wait(timeout)
_shutdown_event = threading.Event()


def _signal_handler(signum, frame):
    _shutdown_event.set()
    logger.info("Shutdown requested — will exit after current operations complete")


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
if hasattr(signal, "SIGBREAK"):
    signal.signal(signal.SIGBREAK, _signal_handler)


def _force_close_browser(browser):
    """Quit browser quickly — kill process if quit() hangs on a dead driver."""
    pid = None
    try:
        pid = browser.driver.service.process.pid
    except Exception:
        pass

    # WS-F: stop the disconnect-popup watcher thread BEFORE quit() so the daemon
    # thread doesn't race with chromedriver tearing down (avoids spurious
    # WebDriverException tracebacks on shutdown).
    try:
        if hasattr(browser, "stop_disconnect_watcher"):
            browser.stop_disconnect_watcher()
    except Exception:
        pass

    try:
        browser.driver.quit()
    except Exception:
        # Browser/ChromeDriver already dead — force-kill the process tree
        if pid:
            try:
                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        timeout=5,
                    )
                else:
                    os.kill(pid, 9)  # SIGKILL
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Symbol fetching
# ---------------------------------------------------------------------------


def fetch_symbols_by_category(batch_size: int) -> tuple[list[list[str]], int]:
    """Fetch symbols from MongoDB and pair within same category.

    Returns (batches, total_count) where each batch contains symbols
    from the same asset class for matching market hours.
    """
    from tte.data.symbols import get_symbols

    logger.info("Fetching symbols from MongoDB...")
    symbols_by_category = get_symbols()

    batches = []
    total = 0
    for category, symbols in symbols_by_category.items():
        logger.info(f"  {category}: {len(symbols)} symbols")
        total += len(symbols)
        for i in range(0, len(symbols), batch_size):
            batches.append(symbols[i : i + batch_size])

    logger.info(f"Total: {total} symbols in {len(batches)} batches of {batch_size}")
    return batches, total


# ---------------------------------------------------------------------------
# Browser setup
# ---------------------------------------------------------------------------


def create_browser(config: ComboConfig, args, layout_override: str = "") -> Browser:
    """Create and initialize a single Browser instance."""
    logger.info("Initializing browser...")

    start_fresh = getattr(args, "fresh", False)
    if start_fresh:
        logger.info("Will delete all existing alerts before setup (--fresh)")

    layout = layout_override or config.layout_name

    # Snapshot layout uses 1h/4h timeframes (set per-snapshot by the worker),
    # not the 45-second screener timeframe which may not exist in the dropdown.
    chart_timeframe = "1 hour" if layout_override else config.chart_timeframe

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
        layout_name=layout,
        chart_timeframe=chart_timeframe,
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
            if _shutdown_event.is_set():
                logger.info("Shutdown requested — stopping")
                break

            batch_start = time()
            logger.info(f"Batch {i + 1}/{len(batches)}: {batch}")

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
                failed.append({"batch": i, "symbols": batch, "error": "change_settings_failed"})
                continue
            t_settings = time() - t0

            t0 = time()
            _shutdown_event.wait(config.recalc_wait)  # Wait for screener recalculation
            if _shutdown_event.is_set():
                break
            t_recalc = time() - t0

            # Check for screener errors
            t0 = time()
            if not browser.is_no_error(config.screener_shorttitle):
                logger.warning("Screener has errors, attempting recovery")

                # Recovery attempt
                indicator_for_reupload = browser._safe_indicator_access(config.screener_shorttitle)
                if not indicator_for_reupload or not browser.reupload_indicator(
                    indicator_for_reupload,
                    config.screener_name,
                    config.screener_shorttitle,
                ):
                    logger.error("Failed to re-upload screener")
                    failed.append({"batch": i, "symbols": batch, "error": "reupload_failed"})
                    continue

                _shutdown_event.wait(config.recalc_wait)  # Wait for indicator to fully load
                if _shutdown_event.is_set():
                    break

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

                _shutdown_event.wait(config.recalc_wait)  # Wait for recalculation
                if _shutdown_event.is_set():
                    break

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
            logger.info(f"  is_no_error check took {t_error_check:.1f}s")

            # Click indicator (is_no_error already validated it exists; get a fresh reference)
            logger.info("  Finding indicator in legend...")
            try:
                indicators = browser.driver.find_elements(
                    By.CSS_SELECTOR, 'div[data-qa-id="legend-source-item"]'
                )
                indicator = None
                for ind in indicators:
                    name = browser.driver.execute_script(
                        'var d = arguments[0].querySelectorAll(\'div[class*="title-"]\'); return d.length > 0 ? d[0].textContent : "";',
                        ind,
                    )
                    if name == config.screener_shorttitle:
                        indicator = ind
                        break
                logger.info(f"  Found indicator in legend: {indicator is not None}")
            except Exception:
                logger.exception("  Exception finding indicator in legend")
                indicator = None

            if not indicator:
                logger.error("Indicator access failed")
                failed.append({"batch": i, "symbols": batch, "error": "indicator_access_failed"})
                continue

            logger.info("  Clicking indicator...")
            indicator.click()
            logger.info("  Indicator clicked. Calling create_webhook_alert...")

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

                retry_indicator = browser._safe_indicator_access(config.screener_shorttitle)
                if retry_indicator and browser.reupload_indicator(
                    retry_indicator, config.screener_name, config.screener_shorttitle
                ):
                    _shutdown_event.wait(config.recalc_wait)

                    if browser.change_settings(batch, config.screener_shorttitle):
                        _shutdown_event.wait(config.recalc_wait)

                        indicator = browser._safe_indicator_access(config.screener_shorttitle)
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
                    failed.append({"batch": i, "symbols": batch, "error": "retry_reupload_failed"})
                    logger.error("Retry failed - re-upload failed")

            _shutdown_event.wait(config.alert_creation_delay)

    except Exception as e:
        if _shutdown_event.is_set():
            logger.debug(f"Alert creation interrupted by shutdown: {e}")
        else:
            logger.exception("Fatal error during alert creation")
        return {
            "completed": completed,
            "failed": failed,
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


def restart_inactive_alerts(driver, browser=None) -> bool:
    """Restart all inactive alerts via TradingView UI.

    Standalone function (no Alerts class dependency). Replicates the Selenium
    steps from handle_alerts.py:240-303.

    The optional `browser` arg enables a login-state guard (2026-05-14): if the
    chart layout has been lost (TV session expired silently), maintenance bails
    out early instead of timing out on every selector. The 2026-05-08 snapshot
    blackout was caused by this exact failure mode going undetected for 6 days.
    """
    if _shutdown_event.is_set():
        return False

    # Login-state guard — bail out cleanly if TV signed us out
    if browser is not None and not browser.ensure_chart_layout_loaded():
        logger.error("Chart layout unavailable during maintenance — skipping this cycle.")
        return False

    utils = Utils()
    try:
        # Make sure that the Alerts tab is open
        utils.open_alert_tab(driver)

        # Click the 3-dot settings button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))
        ).click()

        # Wait for the dropdown to show up
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'))
        )

        # Check if the "Show Alerts" section is minimised. If so, expand it
        show_all_sections = [
            el
            for el in dropdown.find_elements(By.CSS_SELECTOR, "div[data-open]")
            if "Show Alerts" in el.text
        ]
        if show_all_sections:
            show_all_section = show_all_sections[0]
            maximized = show_all_section.get_attribute("data-open") == "true"
            if not maximized:
                show_all_section.click()
                logger.info('Expanded the "Show Alerts" section')

        # Check if the "All" option is selected. If not, select it
        all_options = [
            el
            for el in dropdown.find_elements(By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"] div')
            if el.text.strip() == "All" and el.find_elements(By.TAG_NAME, "input")
        ]
        if all_options and not all_options[0].find_element(By.TAG_NAME, "input").is_selected():
            all_options[0].click()
            logger.info('Selected the "All" option')

        # Find "Restart all inactive" button (may be disabled when no inactive alerts)
        restart_buttons = [
            el
            for el in dropdown.find_elements(By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"] div')
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
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]'))
            )
            popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
            logger.info("Restarting all inactive alerts!")

        _shutdown_event.wait(1)
        return True

    except Exception:
        if _shutdown_event.is_set():
            logger.debug("restart_inactive_alerts interrupted by shutdown")
        else:
            logger.exception("Error restarting inactive alerts:")
        return False


def clear_alert_log(driver) -> bool:
    """Clear the TradingView alert log to prevent it from growing indefinitely."""
    if _shutdown_event.is_set():
        return False

    utils = Utils()
    try:
        utils.open_log_tab(driver)

        # Click clear log button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="clear-log-button"]'))
        ).click()

        # Confirm in dialog
        popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]'))
        )
        popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
        logger.info("Alert log cleared!")
        _shutdown_event.wait(1)
        return True
    except Exception:
        if _shutdown_event.is_set():
            logger.debug("clear_alert_log interrupted by shutdown")
        else:
            logger.exception("Error clearing alert log:")
        return False


def run_maintenance(browser: Browser, config: ComboConfig):
    """Loop: restart inactive alerts + clear log, and poll for snapshots.

    Uses dual timers:
    - Maintenance timer (config.maintenance_interval): restart alerts, clear log, refresh page
    - Snapshot timer (config.snapshot_poll_interval): poll Stock Buddy for pending snapshots

    Handles graceful shutdown via _shutdown_event for interruptible waits.
    """
    interval = config.maintenance_interval
    snapshot_interval = config.snapshot_poll_interval
    tick = min(snapshot_interval, interval)  # Sleep in increments of the shorter timer

    logger.info(
        f"Maintenance loop started (maintenance every {interval}s, "
        f"snapshots every {snapshot_interval}s, tick={tick}s)"
    )

    if _shutdown_event.is_set():
        logger.info("Shutdown already requested — skipping maintenance")
        _force_close_browser(browser)
        return

    # Switch to Snapshot layout for maintenance (covers --maintain-only mode)
    if not browser.change_layout(config.snapshot_layout_name):
        logger.warning(
            f"Failed to switch to '{config.snapshot_layout_name}' layout — "
            "maintenance will run on current layout"
        )
    else:
        logger.info(f"Switched to '{config.snapshot_layout_name}' layout for maintenance")

    if _shutdown_event.is_set():
        logger.info("Shutdown requested — skipping maintenance")
        _force_close_browser(browser)
        return

    # Initialize snapshot worker if enabled
    snapshot_worker = None
    client = None
    if config.snapshot_enabled:
        from tte.snapshot_worker import SnapshotWorker, StockBuddyClient

        client = StockBuddyClient(config)
        snapshot_worker = SnapshotWorker(browser, config, client, _shutdown_event)
        logger.info("Snapshot worker initialized")

        # Trigger backfill to queue old setups without snapshotStatus
        client.trigger_backfill()
    else:
        logger.info("Snapshot worker disabled")

    last_maintenance = 0.0  # Force immediate first maintenance run
    last_snapshot = 0.0  # Force immediate first snapshot check
    last_backfill = time()  # Just ran above; re-trigger every hour
    backfill_interval = 3600  # 1 hour

    try:
        while not _shutdown_event.is_set():
            now = time()
            maintenance_due = now - last_maintenance >= interval

            # --- Maintenance check (runs first — has priority over snapshots) ---
            if maintenance_due:
                if _shutdown_event.is_set():
                    break
                last_maintenance = now
                logger.info("Running maintenance cycle...")
                try:
                    # Refresh page to keep session alive
                    browser.driver.refresh()
                    if _shutdown_event.wait(5):
                        break  # Shutdown during post-refresh wait

                    # Login-state guard (must come BEFORE open_alerts_sidebar — that call
                    # is one of the selectors that times out on the placeholder page).
                    if not browser.ensure_chart_layout_loaded():
                        logger.error("Chart layout unavailable — skipping maintenance cycle.")
                        continue

                    # Re-open alerts sidebar (refresh may close it)
                    browser.open_alerts_sidebar()

                    # Restart inactive alerts
                    restart_inactive_alerts(browser.driver, browser=browser)
                    if _shutdown_event.is_set():
                        break

                    # Clear alert log
                    clear_alert_log(browser.driver)

                    # Reset bars_to_right after refresh (refresh clears chart settings)
                    if snapshot_worker:
                        snapshot_worker._bars_right_last_set = 0

                except Exception:
                    if _shutdown_event.is_set():
                        logger.debug("Maintenance interrupted by shutdown")
                    else:
                        logger.exception("Maintenance cycle failed, will retry next cycle:")

            # --- Snapshot check (now runs after maintenance too) ---
            if (
                snapshot_worker
                and (now - last_snapshot >= snapshot_interval)
                and not _shutdown_event.is_set()
            ):
                # Brief stabilization wait after maintenance refresh
                if maintenance_due and not _shutdown_event.is_set():
                    _shutdown_event.wait(3)

                try:
                    snapshot_worker.process_pending_snapshots()
                except Exception:
                    if _shutdown_event.is_set():
                        logger.debug("Snapshot cycle interrupted by shutdown")
                    else:
                        logger.exception("Snapshot cycle failed, will retry next cycle:")
                last_snapshot = time()  # Set AFTER processing (not before)

            # --- Periodic backfill (every hour) ---
            if client and now - last_backfill >= backfill_interval:
                last_backfill = now
                client.trigger_backfill()

            # Interruptible sleep — returns immediately when shutdown is signaled
            _shutdown_event.wait(tick)

        logger.info("Maintenance loop stopped — cleaning up browser")
    finally:
        _force_close_browser(browser)
        logger.info("Browser closed")


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
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated list of symbols to create alerts for (e.g., NSE:RELIANCE,BSE:ABBOTINDIA). Only these symbols will be batched and processed.",
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
        from urllib.parse import urlparse

        parsed = urlparse(config.webhook_url)
        print(f"  Webhook URL: {parsed.scheme}://{parsed.netloc}/***", flush=True)
        print(f"  Batch size: {config.batch_size}", flush=True)
        print(f"  Creation delay: {config.alert_creation_delay}s", flush=True)
        print(f"  Recalc wait: {config.recalc_wait}s", flush=True)
        print(f"  Maintenance interval: {config.maintenance_interval}s", flush=True)
        sys.exit(0)

    # --- Maintain only mode ---
    if args.maintain_only:
        logger.info("Running maintenance only (--maintain-only)")
        browser = create_browser(config, args, layout_override=config.snapshot_layout_name)
        run_maintenance(browser, config)
        # Browser cleanup is handled in run_maintenance's finally block
        return

    # --- Fetch symbols and create batches ---
    if args.symbols:
        # Use explicit symbol list instead of fetching from MongoDB
        symbol_list = [s.strip() for s in args.symbols.split(",") if s.strip()]
        logger.info(f"Using --symbols filter: {len(symbol_list)} symbols")
        batches = []
        for i in range(0, len(symbol_list), config.batch_size):
            batches.append(symbol_list[i : i + config.batch_size])
        total = len(symbol_list)
        logger.info(f"Total: {total} symbols in {len(batches)} batches of {config.batch_size}")
    else:
        batches, total = fetch_symbols_by_category(config.batch_size)
    if not batches:
        logger.error("No symbols fetched — cannot continue")
        sys.exit(1)

    # --- Initialize browser ---
    browser = create_browser(config, args)

    # --- Ensure regular trading hours (prevents off-hours signals for stocks) ---
    if browser.open_chart.ensure_regular_hours():
        # Save layout so the session setting persists across future sessions
        browser.save_layout()
    else:
        logger.warning("Could not verify session hours setting — continuing anyway")

    # --- Run alert creation ---
    logger.info("Starting alert creation...")
    result = run_alert_creation(browser, batches, config)

    logger.info(f"Finished: {result['completed']}/{result['total']} alerts created")
    if result["failed"]:
        logger.warning(f"{len(result['failed'])} batches failed:")
        for fb in result["failed"]:
            logger.warning(f"  Batch {fb['batch']}: {fb['symbols']} — {fb['error']}")

        # --- Auto-retry failed batches (once) ---
        retry_batches = [fb["symbols"] for fb in result["failed"]]
        retry_total = sum(len(b) for b in retry_batches)
        logger.info(f"Retrying {len(retry_batches)} failed batches ({retry_total} symbols)...")
        retry_result = run_alert_creation(browser, retry_batches, config)
        logger.info(
            f"Retry finished: {retry_result['completed']}/{retry_result['total']} alerts created"
        )
        if retry_result["failed"]:
            logger.warning(f"{len(retry_result['failed'])} batches still failed after retry:")
            for fb in retry_result["failed"]:
                logger.warning(f"  Batch {fb['batch']}: {fb['symbols']} — {fb['error']}")

    # --- Setup only mode ---
    if args.setup_only:
        logger.info("Setup complete (--setup-only). Exiting.")
        _force_close_browser(browser)
        return

    # --- Check shutdown before transitioning to maintenance ---
    if _shutdown_event.is_set():
        logger.info("Shutdown requested — skipping maintenance")
        _force_close_browser(browser)
        return

    # --- Switch to Snapshot layout before maintenance ---
    logger.info("Saving Screener layout and switching to Snapshot layout...")
    browser.save_layout()

    if _shutdown_event.is_set():
        logger.info("Shutdown requested — skipping maintenance")
        _force_close_browser(browser)
        return

    if not browser.change_layout(config.snapshot_layout_name):
        logger.warning(
            f"Failed to switch to '{config.snapshot_layout_name}' layout — "
            "maintenance will run on current layout"
        )

    # --- Maintenance loop (reuse the same browser) ---
    logger.info("Starting maintenance mode...")
    run_maintenance(browser, config)
    # Browser cleanup is handled in run_maintenance's finally block


if __name__ == "__main__":
    main()
