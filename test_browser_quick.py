#!/usr/bin/env python3
"""
Quick Browser Tests for TTE Selenium Automation.

This script helps validate Selenium automation before production use.
Run individual tests to verify specific capabilities.

Usage:
    python test_browser_quick.py --help
    python test_browser_quick.py --test browser
    python test_browser_quick.py --test navigation
    python test_browser_quick.py --test indicator
    python test_browser_quick.py --test alert
    python test_browser_quick.py --test all
    python test_browser_quick.py --inspect-alert   # Opens alert dialog for inspection
"""

import argparse
import sys
import time
from typing import Optional

from config import Config
from selenium_manager import SeleniumManager, SeleniumError, TVSelectors


def test_browser_init() -> bool:
    """Test 1: Verify Chrome browser can be initialized."""
    print("\n=== Test 1: Browser Initialization ===")

    try:
        with SeleniumManager() as browser:
            driver = browser.get_driver()
            print(f"  [OK] Chrome driver initialized")
            print(f"  [OK] Window title: {driver.title}")
            print(f"  [OK] Session ID: {driver.session_id[:20]}...")
            return True
    except SeleniumError as e:
        print(f"  [FAIL] {e}")
        return False


def test_chart_navigation() -> bool:
    """Test 2: Verify navigation to TradingView chart."""
    print("\n=== Test 2: Chart Navigation ===")

    test_url = "https://www.tradingview.com/chart/?symbol=EURUSD"

    try:
        with SeleniumManager() as browser:
            driver = browser.get_driver()
            browser.navigate_to_chart(test_url, wait_time=5)

            print(f"  [OK] Navigated to chart")
            print(f"  [OK] Current URL: {driver.current_url[:50]}...")

            # Check if chart container is present
            try:
                driver.find_element("css selector", TVSelectors.CHART_CONTAINER)
                print(f"  [OK] Chart container found")
            except:
                print(f"  [WARN] Chart container not found (may still work)")

            return True
    except SeleniumError as e:
        print(f"  [FAIL] {e}")
        return False


def test_indicator_settings() -> bool:
    """Test 3: Verify indicator settings can be opened."""
    print("\n=== Test 3: Indicator Settings ===")

    if not Config.NWE_CHART_URL:
        print("  [WARN] NWE_CHART_URL not configured, skipping")
        print("  -> Set NWE_CHART_URL in .env file")
        return False

    try:
        with SeleniumManager() as browser:
            driver = browser.get_driver()

            print(f"  -> Navigating to NWE chart...")
            browser.navigate_to_chart(Config.NWE_CHART_URL, wait_time=5)

            print(f"  -> Looking for TTE NWE Screener indicator...")
            indicators = driver.find_elements("css selector", TVSelectors.LEGEND_ITEM)
            print(f"  [OK] Found {len(indicators)} indicators in legend")

            # List all indicator names
            for i, ind in enumerate(indicators):
                try:
                    title = ind.find_element("css selector", TVSelectors.INDICATOR_TITLE).text
                    print(f"     [{i+1}] {title}")
                except:
                    continue

            # Try to open settings
            print(f"  -> Opening indicator settings...")
            browser.open_indicator_settings("TTE NWE Screener")
            print(f"  [OK] Settings dialog opened")

            # Check for symbol inputs
            dialog = driver.find_element("css selector", TVSelectors.INDICATOR_SETTINGS_DIALOG)
            inputs = dialog.find_elements("css selector", "input[type='text']")
            print(f"  [OK] Found {len(inputs)} text inputs in settings")

            # Click OK to close
            browser.click_ok_button()
            print(f"  [OK] Settings closed")

            return True
    except SeleniumError as e:
        print(f"  [FAIL] {e}")
        return False
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False


def test_alert_creation_ui() -> bool:
    """Test 4: Verify alert creation UI elements are accessible."""
    print("\n=== Test 4: Alert Creation UI ===")

    if not Config.NWE_CHART_URL:
        print("  [WARN] NWE_CHART_URL not configured, skipping")
        return False

    try:
        with SeleniumManager() as browser:
            driver = browser.get_driver()

            print(f"  -> Navigating to chart...")
            browser.navigate_to_chart(Config.NWE_CHART_URL, wait_time=5)

            # Find Set Alert button
            print(f"  -> Looking for Set Alert button...")
            try:
                alert_btn = driver.find_element("css selector", TVSelectors.SET_ALERT_BUTTON)
                print(f"  [OK] Set Alert button found")
            except:
                print(f"  [FAIL] Set Alert button NOT found")
                print(f"    Selector: {TVSelectors.SET_ALERT_BUTTON}")
                return False

            # Click to open alert dialog
            print(f"  -> Opening alert dialog...")
            alert_btn.click()
            time.sleep(2)

            # Check dialog opened
            try:
                dialog = driver.find_element("css selector", TVSelectors.ALERT_DIALOG)
                print(f"  [OK] Alert dialog opened")
            except:
                print(f"  [FAIL] Alert dialog NOT found")
                print(f"    Selector: {TVSelectors.ALERT_DIALOG}")
                return False

            # Check source dropdown
            try:
                dropdown = dialog.find_element("css selector", TVSelectors.ALERT_SOURCE_DROPDOWN)
                print(f"  [OK] Source dropdown found")
            except:
                print(f"  [WARN] Source dropdown not found")
                print(f"    Selector: {TVSelectors.ALERT_SOURCE_DROPDOWN}")

            # Check for alert name input
            try:
                name_input = dialog.find_element("css selector", TVSelectors.ALERT_NAME_INPUT)
                print(f"  [OK] Alert name input found")
            except:
                print(f"  [WARN] Alert name input not found")

            # Check for submit button
            try:
                submit = dialog.find_element("css selector", TVSelectors.SUBMIT_BUTTON)
                print(f"  [OK] Submit button found")
            except:
                print(f"  [WARN] Submit button not found")

            # Close dialog
            try:
                close_btn = dialog.find_element("css selector", TVSelectors.CLOSE_BUTTON)
                close_btn.click()
                print(f"  [OK] Dialog closed")
            except:
                driver.find_element("tag name", "body").send_keys("\ue00c")  # Escape key
                print(f"  [OK] Dialog closed via Escape")

            return True
    except SeleniumError as e:
        print(f"  [FAIL] {e}")
        return False


def inspect_alert_dialog():
    """
    Open alert dialog and keep browser open for manual inspection.

    This helps discover selectors for webhook configuration.
    Use browser dev tools (F12) to inspect elements.
    """
    print("\n=== Alert Dialog Inspection Mode ===")
    print("Browser will stay open for manual inspection.")
    print("Use F12 to open dev tools and inspect elements.")
    print("Press Ctrl+C to exit.\n")

    if not Config.NWE_CHART_URL:
        print("ERROR: NWE_CHART_URL not configured in .env file")
        return

    browser = SeleniumManager()
    try:
        driver = browser.get_driver()
        browser.navigate_to_chart(Config.NWE_CHART_URL, wait_time=5)

        print("-> Opening alert dialog...")
        alert_btn = driver.find_element("css selector", TVSelectors.SET_ALERT_BUTTON)
        alert_btn.click()
        time.sleep(2)

        print("\n" + "="*60)
        print("ALERT DIALOG IS NOW OPEN")
        print("="*60)
        print("\nLook for these elements in the Notifications tab:")
        print("  1. Tab selector (to switch to Notifications)")
        print("  2. Webhook URL toggle/checkbox")
        print("  3. Webhook URL input field")
        print("  4. Message format textarea")
        print("\nCurrent selectors to update in TVSelectors class:")
        print(f"  NOTIFICATIONS_TAB = '{TVSelectors.NOTIFICATIONS_TAB}'")
        print(f"  WEBHOOK_URL_TOGGLE = '{TVSelectors.WEBHOOK_URL_TOGGLE}'")
        print(f"  WEBHOOK_URL_INPUT = '{TVSelectors.WEBHOOK_URL_INPUT}'")
        print(f"  ALERT_MESSAGE_INPUT = '{TVSelectors.ALERT_MESSAGE_INPUT}'")
        print("\n" + "="*60)
        print("Press Ctrl+C when done inspecting...")

        # Keep browser open
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nClosing browser...")
        browser.close()
    except Exception as e:
        print(f"Error: {e}")
        browser.close()


def run_all_tests() -> bool:
    """Run all tests."""
    results = []

    results.append(("Browser Init", test_browser_init()))
    results.append(("Chart Navigation", test_chart_navigation()))
    results.append(("Indicator Settings", test_indicator_settings()))
    results.append(("Alert UI", test_alert_creation_ui()))

    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)

    all_passed = True
    for name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL]"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("="*50)

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Quick browser tests for TTE")
    parser.add_argument(
        "--test",
        choices=["browser", "navigation", "indicator", "alert", "all"],
        help="Test to run"
    )
    parser.add_argument(
        "--inspect-alert",
        action="store_true",
        help="Open alert dialog for manual inspection"
    )

    args = parser.parse_args()

    if args.inspect_alert:
        inspect_alert_dialog()
        return

    if not args.test:
        parser.print_help()
        return

    if args.test == "browser":
        success = test_browser_init()
    elif args.test == "navigation":
        success = test_chart_navigation()
    elif args.test == "indicator":
        success = test_indicator_settings()
    elif args.test == "alert":
        success = test_alert_creation_ui()
    elif args.test == "all":
        success = run_all_tests()
    else:
        parser.print_help()
        return

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
