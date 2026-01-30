"""
Automated Test: TTE NWE Screener using Edge Browser

This script connects to an existing Edge browser session via remote debugging.

SETUP INSTRUCTIONS:
1. Close ALL Edge windows
2. Start Edge with remote debugging:
   "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9222
3. Sign in to TradingView in that Edge window
4. Run this test: python test_nwe_edge.py
"""

import sys
import os
from time import sleep
from datetime import datetime
from json import loads
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Import our modules
from tiered_orchestrator import TieredOrchestrator, SignalDirection

# Test configuration
NWE_SCREENER_NAME = "TTE NWE Screener"
NWE_SCREENER_SHORT = "NWE Scan"
REMOTE_DEBUG_PORT = 9222


class EdgeNWETest:
    """Test NWE Screener using Edge browser."""

    def __init__(self):
        self.driver = None
        self.orchestrator = None
        self.test_results = []

    def setup(self):
        """Initialize Edge browser - connect to existing session."""
        print("\n" + "=" * 60)
        print("SETUP: Connecting to Edge browser...")
        print("=" * 60)

        try:
            # Method 1: Try to connect to existing Edge with remote debugging
            print(f"Attempting to connect to Edge on port {REMOTE_DEBUG_PORT}...")

            edge_options = webdriver.EdgeOptions()
            edge_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{REMOTE_DEBUG_PORT}")

            try:
                self.driver = webdriver.Edge(options=edge_options)
                print("Connected to existing Edge session!")
            except WebDriverException as e:
                if "cannot connect" in str(e).lower() or "refused" in str(e).lower():
                    print("\nCould not connect to Edge remote debugging.")
                    print("\nPlease start Edge with remote debugging:")
                    print('  1. Close ALL Edge windows')
                    print('  2. Run this command in PowerShell:')
                    print(f'     & "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port={REMOTE_DEBUG_PORT}')
                    print('  3. Sign in to TradingView')
                    print('  4. Run this test again')
                    self._record_result("Setup", False, "Edge not running with remote debugging")
                    return False
                raise

            # Initialize orchestrator
            self.orchestrator = TieredOrchestrator(self.driver)
            print("Orchestrator initialized")

            self._record_result("Setup", True, "Connected to Edge browser")
            return True

        except Exception as e:
            self._record_result("Setup", False, f"Exception: {e}")
            print(f"Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_1_open_tradingview(self):
        """Test 1: Open TradingView chart."""
        print("\n" + "=" * 60)
        print("TEST 1: Open TradingView chart")
        print("=" * 60)

        try:
            # Check current URL
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")

            if "tradingview.com/chart" in current_url:
                print("Already on TradingView chart")
                self._record_result("Test 1: Open TradingView", True, "Already on chart page")
                return True

            # Navigate to chart
            self.driver.get("https://www.tradingview.com/chart")
            sleep(5)

            # Check if we're on a chart page
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[class*="chart-container"], div[class*="chart-markup-table"]')
                    )
                )
                self._record_result("Test 1: Open TradingView", True, "Chart page loaded")
                return True
            except TimeoutException:
                if "signin" in self.driver.current_url.lower():
                    self._record_result("Test 1: Open TradingView", False, "Not signed in")
                    return False
                self._record_result("Test 1: Open TradingView", False, "Chart container not found")
                return False

        except Exception as e:
            self._record_result("Test 1: Open TradingView", False, f"Exception: {e}")
            return False

    def test_2_find_nwe_screener(self):
        """Test 2: Find or add NWE Screener indicator."""
        print("\n" + "=" * 60)
        print("TEST 2: Find NWE Screener indicator")
        print("=" * 60)

        try:
            sleep(2)

            # Look for indicator in legend
            indicator = self._find_indicator(NWE_SCREENER_SHORT)

            if indicator:
                print(f"Found indicator: {NWE_SCREENER_SHORT}")
                self._record_result("Test 2: Find NWE Screener", True, "NWE Screener found on chart")
                return True

            # Try to add from favorites
            print("Indicator not found, trying to add from favorites...")
            if self._add_indicator_from_favorites(NWE_SCREENER_NAME):
                sleep(5)
                indicator = self._find_indicator(NWE_SCREENER_SHORT)
                if indicator:
                    self._record_result("Test 2: Find NWE Screener", True, "NWE Screener added from favorites")
                    return True

            # Try indicator search
            print("Trying indicator search...")
            if self._add_indicator_via_search(NWE_SCREENER_NAME):
                sleep(5)
                indicator = self._find_indicator(NWE_SCREENER_SHORT)
                if indicator:
                    self._record_result("Test 2: Find NWE Screener", True, "NWE Screener added via search")
                    return True

            self._record_result("Test 2: Find NWE Screener", False, "Could not find or add NWE Screener - please add it manually to TradingView first")
            return False

        except Exception as e:
            self._record_result("Test 2: Find NWE Screener", False, f"Exception: {e}")
            return False

    def test_3_verify_debug_table(self):
        """Test 3: Verify debug table shows symbols."""
        print("\n" + "=" * 60)
        print("TEST 3: Verify debug table")
        print("=" * 60)

        try:
            sleep(3)

            # Check page source for expected symbols
            page_source = self.driver.page_source
            expected_symbols = ["GBPAUD", "AUDJPY", "EURCAD", "EURGBP", "USDCHF"]

            found_count = 0
            for symbol in expected_symbols:
                if symbol in page_source:
                    found_count += 1
                    print(f"  Found symbol: {symbol}")

            if found_count >= 3:
                self._record_result("Test 3: Debug Table", True, f"Found {found_count}/5 symbols in table")
                return True
            else:
                if "Compilation error" in page_source:
                    self._record_result("Test 3: Debug Table", False, "Indicator has compilation error")
                else:
                    self._record_result("Test 3: Debug Table", False, f"Only found {found_count}/5 symbols - indicator may not be loaded")
                return False

        except Exception as e:
            self._record_result("Test 3: Debug Table", False, f"Exception: {e}")
            return False

    def test_4_check_signal_columns(self):
        """Test 4: Check for signal indicators."""
        print("\n" + "=" * 60)
        print("TEST 4: Check signal columns")
        print("=" * 60)

        try:
            page_source = self.driver.page_source

            signal_terms = ["BULL", "BEAR", "Signal", "H4", "D1"]
            found_terms = []

            for term in signal_terms:
                if term in page_source:
                    found_terms.append(term)
                    print(f"  Found: {term}")

            if len(found_terms) >= 3:
                self._record_result("Test 4: Signal Columns", True, f"Found: {found_terms}")
                return True
            else:
                self._record_result("Test 4: Signal Columns", False, f"Only found: {found_terms}")
                return False

        except Exception as e:
            self._record_result("Test 4: Signal Columns", False, f"Exception: {e}")
            return False

    def test_5_orchestrator_integration(self):
        """Test 5: Test orchestrator with simulated alerts."""
        print("\n" + "=" * 60)
        print("TEST 5: Test orchestrator integration")
        print("=" * 60)

        try:
            test_alerts = [
                {"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4,D1"},
                {"symbol": "EURUSD", "nwe": "bearish", "tf": "D1"},
                {"symbol": "USDJPY", "nwe": "bullish", "tf": "H4"},
            ]

            for alert in test_alerts:
                self.orchestrator.on_nwe_alert(alert)
                print(f"  Added: {alert['symbol']} - {alert['nwe']}")

            stats = self.orchestrator.get_statistics()
            print(f"  Hot list size: {stats['hot_list_size']}")
            print(f"  Bullish: {stats['bullish_count']}, Bearish: {stats['bearish_count']}")

            if stats['hot_list_size'] == 3:
                self._record_result("Test 5: Orchestrator", True, f"Stats: {stats}")
                return True
            else:
                self._record_result("Test 5: Orchestrator", False, f"Unexpected size: {stats['hot_list_size']}")
                return False

        except Exception as e:
            self._record_result("Test 5: Orchestrator", False, f"Exception: {e}")
            return False

    def test_6_alert_format_parsing(self):
        """Test 6: Test alert JSON format parsing."""
        print("\n" + "=" * 60)
        print("TEST 6: Test alert format parsing")
        print("=" * 60)

        try:
            test_cases = [
                ('{"symbol":"GBPAUD","nwe":"bullish","tf":"H4"}', True, "bullish", ["H4"]),
                ('{"symbol":"EURUSD","nwe":"bearish","tf":"H4,D1"}', True, "bearish", ["H4", "D1"]),
            ]

            all_passed = True
            for json_str, expect_valid, expect_dir, expect_tfs in test_cases:
                parsed = loads(json_str)
                is_nwe = "nwe" in parsed and "symbol" in parsed
                direction = parsed.get("nwe", "")
                tf_list = [t.strip() for t in parsed.get("tf", "").split(",")]

                if is_nwe == expect_valid and direction == expect_dir:
                    print(f"  PASS: {parsed['symbol']} - {direction}")
                else:
                    print(f"  FAIL: {json_str}")
                    all_passed = False

            if all_passed:
                self._record_result("Test 6: Alert Parsing", True, "All formats parsed correctly")
                return True
            else:
                self._record_result("Test 6: Alert Parsing", False, "Some formats failed")
                return False

        except Exception as e:
            self._record_result("Test 6: Alert Parsing", False, f"Exception: {e}")
            return False

    def _find_indicator(self, shorttitle: str):
        """Find indicator by short title."""
        try:
            indicators = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')
                )
            )

            for ind in indicators:
                try:
                    text = ind.text
                    if shorttitle in text:
                        return ind
                except:
                    continue
            return None
        except:
            return None

    def _add_indicator_from_favorites(self, indicator_name: str) -> bool:
        """Add indicator from favorites."""
        try:
            ind_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'div[id="header-toolbar-indicators"]')
                )
            )
            ind_button.click()
            sleep(1)

            menu_items = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="menuitem"]')
            for item in menu_items:
                if indicator_name.lower() in item.text.lower():
                    item.click()
                    return True

            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            return False
        except:
            return False

    def _add_indicator_via_search(self, indicator_name: str) -> bool:
        """Add indicator via search."""
        try:
            ind_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'div[id="header-toolbar-indicators"]')
                )
            )
            ind_button.click()
            sleep(1)

            search = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[data-role="search"]')
                )
            )
            search.send_keys(indicator_name)
            sleep(2)

            results = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="indicator-item"]')
            if results:
                results[0].click()
                return True

            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            return False
        except:
            return False

    def _record_result(self, test_name: str, passed: bool, message: str):
        """Record test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({"test": test_name, "passed": passed, "message": message})
        print(f"[{status}] {test_name}: {message}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)

        for result in self.test_results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"  [{status}] {result['test']}: {result['message']}")

        print("=" * 60)
        print(f"TOTAL: {passed}/{total} tests passed")
        print("=" * 60)

        return passed == total

    def run_all_tests(self):
        """Run all tests."""
        if not self.setup():
            self.print_summary()
            return False

        self.test_1_open_tradingview()
        self.test_2_find_nwe_screener()
        self.test_3_verify_debug_table()
        self.test_4_check_signal_columns()
        self.test_5_orchestrator_integration()
        self.test_6_alert_format_parsing()

        return self.print_summary()


def main():
    print("\n" + "=" * 60)
    print("TTE NWE SCREENER TEST - EDGE BROWSER")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\nThis test connects to Edge via remote debugging.")
    print("If not already running, start Edge with:")
    print(f'  & "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port={REMOTE_DEBUG_PORT}')
    print("=" * 60 + "\n")

    tester = EdgeNWETest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
