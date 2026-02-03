#!/usr/bin/env python3
"""
TTE Tiered Orchestrator - Entry Point

This is the main entry point for the TTE Tiered Orchestrator system.
It coordinates the two-tier symbol scanning workflow.

Usage:
    python tiered_main.py                  # Run continuously
    python tiered_main.py --single-cycle   # Run one cycle only
    python tiered_main.py --validate       # Validate configuration
    python tiered_main.py --test-api       # Test API connection
    python tiered_main.py --stats          # Show system statistics
"""

import os

# Skip MongoDB symbols loading - tiered orchestrator gets symbols from API
os.environ["SKIP_MONGODB_SYMBOLS"] = "true"

import argparse
import sys
import logging

import logger_setup
from config import config
from api_client import StockBuddyAPIClient

# Set up logger
logger = logger_setup.setup_logger(__name__, logger_setup.INFO)


def validate_config() -> bool:
    """Validate the configuration and print results."""
    print("Validating configuration...")
    print()

    errors = config.validate()

    print(f"API Base URL: {config.api_base_url}")
    print(f"NWE Chart URL: {config.nwe_chart_url or '(not set)'}")
    print(f"OBDIV Chart URL: {config.obdiv_chart_url or '(not set)'}")
    print(f"NWE Batch Size: {config.nwe_batch_size}")
    print(f"OBDIV Batch Size: {config.obdiv_batch_size}")
    print(f"NWE Batch Wait: {config.nwe_batch_wait}s")
    print(f"OBDIV Batch Wait: {config.obdiv_batch_wait}s")
    print(f"Chrome Profile: {config.chrome_profile}")
    print(f"Cycle Interval: {config.cycle_interval}s")
    print()

    if errors:
        print("Configuration INVALID:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("Configuration VALID")
        return True


def test_api() -> bool:
    """Test API connection and print results."""
    print("Testing API connection...")
    print()

    api = StockBuddyAPIClient(config.api_base_url, config.api_timeout)

    # Health check
    print(f"API Base URL: {config.api_base_url}")
    health_ok = api.health_check()
    print(f"Health check: {'PASS' if health_ok else 'FAIL'}")

    if not health_ok:
        print("\nAPI health check failed. Check that the API is running.")
        return False

    # Get stats
    stats = api.get_stats()
    if stats:
        print("\nAPI Statistics:")
        print(f"  Total symbols: {stats.get('total_symbols', 'N/A')}")
        print(f"  Scanned today: {stats.get('scanned_today', 'N/A')}")
        print(f"  Hot symbols: {stats.get('hot_symbol_count', 'N/A')}")
        print(f"  Current batch: {stats.get('current_batch', 'N/A')}")
    else:
        print("\nCould not retrieve stats (non-critical)")

    # Test getting a batch with configured size
    print(f"\nTesting batch fetch (size={config.nwe_batch_size})...")
    batch = api.get_next_symbol_batch(config.nwe_batch_size)
    if batch.get("success"):
        symbols = batch.get("batch", [])
        print(f"  Batch #{batch.get('batch_number', '?')}: {len(symbols)} symbols")
        print(
            f"  Rotation: {batch.get('rotation_number', '?')} "
            f"({batch.get('symbols_scanned_this_rotation', '?')}/{batch.get('total_symbols', '?')} scanned)"
        )
        if symbols:
            sample = symbols[:3]
            print(
                f"  Sample: {[s['symbol'] if isinstance(s, dict) else s for s in sample]}"
            )
        if len(symbols) == config.nwe_batch_size:
            print(
                f"  Batch size: PASS (got {len(symbols)}, expected {config.nwe_batch_size})"
            )
    else:
        print(f"  Batch fetch failed: {batch.get('error', 'Unknown error')}")

    api.close()
    print("\nAPI test completed successfully!")
    return True


def show_stats():
    """Fetch and display system statistics."""
    print("Fetching system statistics...")
    print()

    api = StockBuddyAPIClient(config.api_base_url, config.api_timeout)

    stats = api.get_stats()
    if not stats:
        print("Could not retrieve statistics from API")
        api.close()
        return

    print("=== TTE System Statistics ===")
    print()
    print(f"Total Symbols: {stats.get('total_symbols', 'N/A')}")
    print(f"Scanned Today: {stats.get('scanned_today', 'N/A')}")
    print(f"Current Batch: {stats.get('current_batch', 'N/A')}")
    print(f"Current Rotation: {stats.get('current_rotation', 'N/A')}")
    print(f"Progress: {stats.get('progress_percent', 'N/A')}%")
    print()
    print(f"Hot Symbols (pending Tier 2): {stats.get('hot_symbol_count', 'N/A')}")
    print(f"Total Signals: {stats.get('total_signals', 'N/A')}")
    print()

    # Get hot symbols
    hot = api.get_hot_symbols(limit=10)
    if hot:
        print("Hot Symbols (top 10):")
        for h in hot:
            symbol = h.get("symbol", "?")
            direction = h.get("direction", "?")
            timeframes = h.get("nwe_timeframes", [])
            print(f"  - {symbol}: {direction} ({', '.join(timeframes)})")
    else:
        print("No hot symbols pending Tier 2")

    api.close()


def test_browser() -> bool:
    """Test browser automation and print results."""
    print("Testing browser automation...")
    print()

    try:
        from open_tv import Browser

        print("Initializing Chrome browser...")
        browser = Browser(
            keep_open=True,
            screener_shorttitle="",
            screener_name="",
            drawer_shorttitle="",
            drawer_name="",
            interval_minutes=10,
            start_fresh=False,
            screener_ob_short="TTE NWE Screener",
            screener_ob_name="TTE NWE Screener",
            screener_nw_short="TTE OBDIV Screener",
            screener_nw_name="TTE OBDIV Screener",
            screener_sb_short="",
            screener_sb_name="",
        )

        print("Browser initialized: PASS")

        # Test navigation
        test_url = config.nwe_chart_url or "https://www.tradingview.com/chart/"
        print(f"Navigating to: {test_url}")
        browser.driver.get(test_url)

        import time

        time.sleep(3)

        print(f"Current URL: {browser.driver.current_url}")
        print("Navigation: PASS")

        # Check if logged in
        print("Checking login status...")
        page_source = browser.driver.page_source
        if "Sign in" in page_source and "Sign up" in page_source:
            print("Login status: NOT LOGGED IN")
            print(
                "Please log in to TradingView manually before running the orchestrator."
            )
        else:
            print("Login status: LOGGED IN")

        print()
        print("Browser test completed successfully!")
        print("Note: Browser window left open for inspection. Close it manually.")
        return True

    except Exception as e:
        print(f"Browser test FAILED: {e}")
        return False


def test_phase2() -> bool:
    """Test Phase 2 (OBDIV) with mock hot symbols."""
    print("Testing Phase 2 (OBDIV) with mock hot symbols...")
    print()

    # Mock hot symbols for testing - these are common forex pairs
    MOCK_HOT_SYMBOLS = [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "USDCAD",
        "NZDUSD",
        "USDCHF",
        "EURGBP",
    ]

    print(f"Mock hot symbols: {MOCK_HOT_SYMBOLS}")
    print()

    try:
        from orchestrator import (
            create_orchestrator,
            OBDIV_LAYOUT_NAME,
            OBDIV_SCREENER_SHORTTITLE,
        )
        import time

        # Create orchestrator (this sets up browser, signs in, etc.)
        print("Initializing orchestrator...")
        orchestrator = create_orchestrator(config)
        print("Orchestrator initialized!")
        print()

        # Switch to OBDIV layout
        print(f"Switching to {OBDIV_LAYOUT_NAME} layout...")
        is_first = not orchestrator._obdiv_layout_initialized
        if not orchestrator._switch_to_layout_with_setup(OBDIV_LAYOUT_NAME, is_first):
            print(f"ERROR: Could not switch to {OBDIV_LAYOUT_NAME} layout")
            return False
        orchestrator._obdiv_layout_initialized = True
        print(f"Switched to {OBDIV_LAYOUT_NAME} layout: PASS")
        print()

        # Input mock symbols into OBDIV screener
        print(f"Inputting {len(MOCK_HOT_SYMBOLS)} mock symbols into OBDIV screener...")
        if not orchestrator._input_symbols_to_screener(
            MOCK_HOT_SYMBOLS, OBDIV_SCREENER_SHORTTITLE
        ):
            print("ERROR: Failed to input symbols into OBDIV screener")
            return False
        print("Symbols input: PASS")
        print()

        # Give the screener time to recalculate
        print("Waiting 3s for screener to recalculate...")
        time.sleep(3)

        # Click on the OBDIV screener indicator
        print(f"Clicking on {OBDIV_SCREENER_SHORTTITLE} indicator...")
        obdiv_indicator = orchestrator.browser._safe_indicator_access(
            OBDIV_SCREENER_SHORTTITLE
        )
        if not obdiv_indicator:
            print(f"ERROR: Could not find {OBDIV_SCREENER_SHORTTITLE} indicator")
            return False
        obdiv_indicator.click()
        print("Indicator clicked: PASS")
        print()

        # Create webhook alert
        print(f"Creating webhook alert for {OBDIV_SCREENER_SHORTTITLE}...")
        print(f"Webhook URL: {orchestrator.obdiv_webhook_url}")
        if not orchestrator.browser.create_webhook_alert(
            OBDIV_SCREENER_SHORTTITLE, orchestrator.obdiv_webhook_url
        ):
            print("ERROR: Failed to create webhook alert")
            return False
        print("Webhook alert created: PASS")
        print()

        # Wait for webhook
        wait_time = config.obdiv_batch_wait
        print(f"Waiting {wait_time}s for webhook to fire...")
        time.sleep(wait_time)
        print("Wait complete")
        print()

        # Delete the alert
        print("Deleting alerts...")
        if not orchestrator.browser.delete_all_alerts():
            print("WARNING: Failed to delete alerts")
        else:
            print("Alerts deleted: PASS")
        print()

        print("=" * 50)
        print("Phase 2 test completed successfully!")
        print("=" * 50)
        print()
        print("Note: Browser window left open for inspection. Close it manually.")
        return True

    except Exception as e:
        print(f"Phase 2 test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_orchestrator(single_cycle: bool = False):
    """Run the tiered orchestrator."""
    print("Starting TTE Tiered Orchestrator...")
    print()

    # Validate configuration first
    if not config.is_valid():
        print("Configuration is invalid. Run with --validate to see errors.")
        sys.exit(1)

    # Start log trimming
    logger_setup.start_continuous_trim("app_log.log")

    logger.info("=" * 60)
    logger.info("TTE Tiered Orchestrator Starting")
    logger.info("=" * 60)

    try:
        from orchestrator import create_orchestrator

        orchestrator = create_orchestrator(config)
        orchestrator.run(single_cycle=single_cycle)

    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user")
        print("\nStopped by user.")
    except Exception as e:
        logger.exception(f"Orchestrator error: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="TTE Tiered Orchestrator - Automated symbol scanning system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tiered_main.py               Run continuously
  python tiered_main.py --single-cycle  Run one cycle only
  python tiered_main.py --validate     Check configuration
  python tiered_main.py --test-api     Test API connection
  python tiered_main.py --stats        Show system statistics
        """,
    )

    parser.add_argument(
        "--validate", action="store_true", help="Validate configuration and exit"
    )
    parser.add_argument(
        "--test-api", action="store_true", help="Test API connection and exit"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show system statistics and exit"
    )
    parser.add_argument(
        "--single-cycle", action="store_true", help="Run only one cycle then exit"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize/reset rotation state (not yet implemented)",
    )
    parser.add_argument(
        "--test-browser", action="store_true", help="Test browser automation and exit"
    )
    parser.add_argument(
        "--test-phase2",
        action="store_true",
        help="Test Phase 2 (OBDIV) with mock hot symbols",
    )

    args = parser.parse_args()

    # Handle command-line options
    if args.validate:
        success = validate_config()
        sys.exit(0 if success else 1)

    if args.test_api:
        success = test_api()
        sys.exit(0 if success else 1)

    if args.stats:
        show_stats()
        sys.exit(0)

    if args.init:
        print("Init command not yet implemented")
        print("Use the Stock Buddy dashboard to reset rotation state")
        sys.exit(0)

    if args.test_browser:
        success = test_browser()
        sys.exit(0 if success else 1)

    if args.test_phase2:
        success = test_phase2()
        sys.exit(0 if success else 1)

    # Run the orchestrator
    run_orchestrator(single_cycle=args.single_cycle)


if __name__ == "__main__":
    main()
