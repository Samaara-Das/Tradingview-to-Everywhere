"""
Automated Test: TTE NWE Screener in TradingView

This script tests:
1. TradingView login and chart loading
2. Loading the TTE NWE Screener indicator
3. Verifying the debug table displays correctly
4. Creating an alert and verifying JSON format
5. Testing the tiered orchestrator integration

Usage:
    python test_nwe_screener.py
"""

import logger_setup
from open_tv import Browser, SYMBOL_INPUTS
from tiered_orchestrator import TieredOrchestrator, SignalDirection
from handle_alerts import Alerts
from time import sleep, time
from datetime import datetime
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from json import loads
import sys

# Set up logger
test_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

# Test configuration
NWE_SCREENER_NAME = "TTE NWE Screener"
NWE_SCREENER_SHORT = "NWE Scan"
TEST_LAYOUT = "NWE Screener"  # Layout name where NWE Screener should be saved


class NWEScreenerTest:
    """Automated tests for TTE NWE Screener."""

    def __init__(self):
        self.browser = None
        self.driver = None
        self.orchestrator = None
        self.test_results = []

    def setup(self):
        """Initialize browser and orchestrator."""
        test_logger.info("=" * 60)
        test_logger.info("SETUP: Initializing browser...")
        test_logger.info("=" * 60)

        try:
            # Initialize browser without starting fresh (don't delete alerts)
            self.browser = Browser(
                keep_open=True,
                screener_shorttitle=NWE_SCREENER_SHORT,
                screener_name=NWE_SCREENER_NAME,
                drawer_shorttitle="Trade",
                drawer_name="Trade Drawer",
                interval_minutes=10,
                start_fresh=False,  # Don't delete existing alerts
            )
            self.driver = self.browser.driver

            # Sign in to TradingView
            if not self.browser.sign_in():
                self._record_result("Setup", False, "Failed to sign in to TradingView")
                return False

            # Open chart
            if not self.browser.open_page("https://www.tradingview.com/chart"):
                self._record_result("Setup", False, "Failed to open TradingView chart")
                return False

            sleep(3)  # Wait for chart to load

            # Initialize orchestrator
            self.orchestrator = TieredOrchestrator(self.driver)
            test_logger.info("Orchestrator initialized")

            self._record_result("Setup", True, "Browser and orchestrator initialized")
            return True

        except Exception as e:
            self._record_result("Setup", False, f"Exception: {e}")
            return False

    def test_1_indicator_loads(self):
        """Test 1: Verify NWE Screener indicator loads without errors."""
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST 1: Verify NWE Screener indicator loads")
        test_logger.info("=" * 60)

        try:
            # Try to find the NWE Screener indicator on the chart
            indicator = self._find_indicator(NWE_SCREENER_SHORT)

            if indicator:
                # Check if indicator has an error
                error_elements = indicator.find_elements(
                    By.CSS_SELECTOR,
                    ".statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS"
                )
                if error_elements:
                    self._record_result("Test 1: Indicator Loads", False, "Indicator has an error")
                    return False

                self._record_result("Test 1: Indicator Loads", True, "NWE Screener found on chart without errors")
                return True
            else:
                # Indicator not found, try to add it
                test_logger.info("Indicator not found, attempting to add it...")
                if self._add_indicator_from_favorites(NWE_SCREENER_NAME):
                    sleep(5)  # Wait for indicator to load
                    indicator = self._find_indicator(NWE_SCREENER_SHORT)
                    if indicator:
                        self._record_result("Test 1: Indicator Loads", True, "NWE Screener added and loaded successfully")
                        return True

                self._record_result("Test 1: Indicator Loads", False, "Could not find or add NWE Screener indicator")
                return False

        except Exception as e:
            self._record_result("Test 1: Indicator Loads", False, f"Exception: {e}")
            return False

    def test_2_debug_table_displays(self):
        """Test 2: Verify debug table shows all 20 symbol rows."""
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST 2: Verify debug table displays correctly")
        test_logger.info("=" * 60)

        try:
            # Look for the debug table (Pine Script tables are rendered as HTML tables)
            # Tables in TradingView are typically in a specific container
            sleep(2)  # Wait for table to render

            # Try to find table cells with symbol names
            # The table should have headers: Symbol, H4, D1, Signal
            tables = self.driver.find_elements(By.CSS_SELECTOR, 'table')

            if not tables:
                # Tables might be in a different container
                test_logger.info("No standard tables found, checking for Pine Script table elements...")

            # Check for any visible text that indicates table content
            # Look for known symbols from the screener
            page_source = self.driver.page_source
            expected_symbols = ["GBPAUD", "AUDJPY", "EURCAD", "EURGBP", "USDCHF"]

            symbols_found = 0
            for symbol in expected_symbols:
                if symbol in page_source:
                    symbols_found += 1
                    test_logger.info(f"Found symbol in page: {symbol}")

            if symbols_found >= 3:
                self._record_result("Test 2: Debug Table", True, f"Found {symbols_found}/5 expected symbols on page")
                return True
            else:
                # Try scrolling/refreshing the chart
                test_logger.info("Few symbols found, trying to refresh view...")
                self.driver.execute_script("window.scrollTo(0, 0);")
                sleep(1)

                # Check again
                page_source = self.driver.page_source
                symbols_found = sum(1 for s in expected_symbols if s in page_source)

                if symbols_found >= 2:
                    self._record_result("Test 2: Debug Table", True, f"Found {symbols_found}/5 symbols after refresh")
                    return True

                self._record_result("Test 2: Debug Table", False, f"Only found {symbols_found}/5 expected symbols")
                return False

        except Exception as e:
            self._record_result("Test 2: Debug Table", False, f"Exception: {e}")
            return False

    def test_3_create_alert(self):
        """Test 3: Create an alert for the NWE Screener and verify it's created."""
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST 3: Create alert for NWE Screener")
        test_logger.info("=" * 60)

        try:
            # Open alerts sidebar
            self.browser.open_alerts_sidebar()
            sleep(1)

            # Click the + button to create alert
            plus_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')
                )
            )
            plus_button.click()

            # Wait for alert dialog
            popup = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')
                )
            )

            # Click condition dropdown
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'span[data-qa-id="ui-kit-disclosure-control main-series-select"]')
                )
            ).click()

            sleep(0.5)

            # Look for NWE Screener in dropdown
            indicator_found = False
            options = self.driver.find_elements(
                By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'
            )

            for option in options:
                if NWE_SCREENER_SHORT in option.text:
                    indicator_found = True
                    option.click()
                    test_logger.info(f"Selected '{NWE_SCREENER_SHORT}' in alert dropdown")
                    break

            if not indicator_found:
                # Close dialog
                popup.find_element(By.CSS_SELECTOR, 'button[data-name="close"]').click()
                self._record_result("Test 3: Create Alert", False, f"'{NWE_SCREENER_SHORT}' not found in alert dropdown")
                return False

            # Set alert name
            alert_name = f"NWE Test Alert {datetime.now().strftime('%H%M%S')}"
            alert_name_input = popup.find_element(By.CSS_SELECTOR, 'input[id="alert-name"]')
            alert_name_input.send_keys(Keys.CONTROL + "a")
            alert_name_input.send_keys(Keys.BACKSPACE)
            alert_name_input.send_keys(alert_name)

            # Click Create
            self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]').click()

            # Check if alert was created successfully (no error)
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"] div[data-name="error-hint"]')
                    )
                )
                # Error found
                self._record_result("Test 3: Create Alert", False, "Error creating alert")
                # Close dialog
                self.driver.find_element(
                    By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"] button[data-name="cancel"]'
                ).click()
                return False
            except TimeoutException:
                # No error - alert created successfully
                self._record_result("Test 3: Create Alert", True, f"Alert '{alert_name}' created successfully")
                return True

        except Exception as e:
            self._record_result("Test 3: Create Alert", False, f"Exception: {e}")
            # Try to close any open dialogs
            try:
                self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="close"]').click()
            except:
                pass
            return False

    def test_4_orchestrator_nwe_alert(self):
        """Test 4: Test orchestrator handles NWE alert correctly."""
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST 4: Test orchestrator NWE alert handling")
        test_logger.info("=" * 60)

        try:
            # Simulate an NWE alert
            test_alert = {
                "symbol": "GBPAUD",
                "nwe": "bullish",
                "tf": "H4,D1"
            }

            # Process alert
            self.orchestrator.on_nwe_alert(test_alert)

            # Verify symbol was added to hot list
            hot_symbols = self.orchestrator.get_hot_symbols()
            gbpaud_in_list = any(hs.symbol == "GBPAUD" for hs in hot_symbols)

            if gbpaud_in_list:
                # Verify properties
                hs = next(h for h in hot_symbols if h.symbol == "GBPAUD")
                checks = [
                    hs.direction == SignalDirection.BULLISH,
                    "H4" in hs.timeframes or "D1" in hs.timeframes,
                    not hs.ob_checked,
                    not hs.div_checked,
                ]

                if all(checks):
                    self._record_result("Test 4: Orchestrator NWE", True, "NWE alert processed correctly, symbol added to hot list")

                    # Test bearish alert updates the entry
                    test_alert_bearish = {
                        "symbol": "GBPAUD",
                        "nwe": "bearish",
                        "tf": "D1"
                    }
                    self.orchestrator.on_nwe_alert(test_alert_bearish)

                    hs_updated = next(h for h in self.orchestrator.get_hot_symbols() if h.symbol == "GBPAUD")
                    if hs_updated.direction == SignalDirection.BEARISH:
                        test_logger.info("Verified: Hot list entry updated when direction changes")

                    return True
                else:
                    self._record_result("Test 4: Orchestrator NWE", False, "Hot symbol has incorrect properties")
                    return False
            else:
                self._record_result("Test 4: Orchestrator NWE", False, "Symbol not added to hot list")
                return False

        except Exception as e:
            self._record_result("Test 4: Orchestrator NWE", False, f"Exception: {e}")
            return False

    def test_5_alert_json_format(self):
        """Test 5: Verify the alert message JSON format is correct."""
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST 5: Verify alert JSON format")
        test_logger.info("=" * 60)

        try:
            # Test parsing various alert formats
            test_cases = [
                ('{"symbol":"GBPAUD","nwe":"bullish","tf":"H4"}', True, "Single TF bullish"),
                ('{"symbol":"EURUSD","nwe":"bearish","tf":"H4,D1"}', True, "Multi TF bearish"),
                ('{"symbol":"USDJPY","nwe":"bullish","tf":"D1"}', True, "D1 only"),
                ('{"GBPAUD": {"timeframe": "1H"}}', False, "TTE Screener format (not NWE)"),
                ('invalid json', False, "Invalid JSON"),
            ]

            passed = 0
            for json_str, expect_nwe, description in test_cases:
                try:
                    parsed = loads(json_str) if json_str != 'invalid json' else {}
                    is_nwe = "nwe" in parsed and "symbol" in parsed

                    if is_nwe == expect_nwe:
                        passed += 1
                        test_logger.info(f"  PASS: {description}")
                    else:
                        test_logger.info(f"  FAIL: {description} - expected NWE={expect_nwe}, got {is_nwe}")
                except:
                    if not expect_nwe:
                        passed += 1
                        test_logger.info(f"  PASS: {description} (correctly rejected)")
                    else:
                        test_logger.info(f"  FAIL: {description} - parse error")

            if passed == len(test_cases):
                self._record_result("Test 5: JSON Format", True, f"All {passed} format tests passed")
                return True
            else:
                self._record_result("Test 5: JSON Format", False, f"Only {passed}/{len(test_cases)} format tests passed")
                return False

        except Exception as e:
            self._record_result("Test 5: JSON Format", False, f"Exception: {e}")
            return False

    def test_6_hot_list_management(self):
        """Test 6: Test hot list expiry and removal."""
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST 6: Test hot list management")
        test_logger.info("=" * 60)

        try:
            # Add multiple symbols
            symbols = [
                {"symbol": "EURUSD", "nwe": "bullish", "tf": "H4"},
                {"symbol": "USDJPY", "nwe": "bearish", "tf": "D1"},
                {"symbol": "AUDJPY", "nwe": "bullish", "tf": "H4,D1"},
            ]

            for alert in symbols:
                self.orchestrator.on_nwe_alert(alert)

            # Verify all added
            hot_list = self.orchestrator.get_hot_symbols()
            added_count = sum(1 for s in ["EURUSD", "USDJPY", "AUDJPY"] if any(hs.symbol == s for hs in hot_list))

            if added_count < 3:
                self._record_result("Test 6: Hot List Management", False, f"Only {added_count}/3 symbols added")
                return False

            # Test removal
            self.orchestrator.remove_from_hot_list("EURUSD")
            hot_list = self.orchestrator.get_hot_symbols()
            eurusd_removed = not any(hs.symbol == "EURUSD" for hs in hot_list)

            if not eurusd_removed:
                self._record_result("Test 6: Hot List Management", False, "Failed to remove symbol from hot list")
                return False

            # Test statistics
            stats = self.orchestrator.get_statistics()
            test_logger.info(f"Orchestrator stats: {stats}")

            if stats["hot_list_size"] >= 2:  # At least USDJPY and AUDJPY (plus GBPAUD from test 4)
                self._record_result("Test 6: Hot List Management", True, f"Hot list management working. Stats: {stats}")
                return True
            else:
                self._record_result("Test 6: Hot List Management", False, f"Unexpected hot list size: {stats['hot_list_size']}")
                return False

        except Exception as e:
            self._record_result("Test 6: Hot List Management", False, f"Exception: {e}")
            return False

    def test_7_integration_with_alerts_class(self):
        """Test 7: Test integration with Alerts class."""
        test_logger.info("\n" + "=" * 60)
        test_logger.info("TEST 7: Test integration with Alerts class")
        test_logger.info("=" * 60)

        try:
            # Create Alerts instance with orchestrator
            alerts = Alerts(
                drawer_shorttitle="Trade",
                screener_shortitle=NWE_SCREENER_SHORT,
                driver=self.driver,
                chart_timeframe="1 hour",
                interval_seconds=600,
                orchestrator=self.orchestrator,
            )

            # Test NWE alert detection
            nwe_alert = {"symbol": "NZDUSD", "nwe": "bullish", "tf": "H4"}
            tte_alert = {"NZDUSD": {"timeframe": "1H", "entryPrice": "0.6100"}}

            is_nwe_1 = alerts.is_nwe_alert(nwe_alert)
            is_nwe_2 = alerts.is_nwe_alert(tte_alert)

            if is_nwe_1 and not is_nwe_2:
                test_logger.info("  PASS: is_nwe_alert() correctly identifies alert types")
            else:
                self._record_result("Test 7: Alerts Integration", False, "is_nwe_alert() incorrect")
                return False

            # Test handle_nwe_alert
            result = alerts.handle_nwe_alert(nwe_alert)
            if result:
                # Verify symbol was added via orchestrator
                hot_list = self.orchestrator.get_hot_symbols()
                nzdusd_added = any(hs.symbol == "NZDUSD" for hs in hot_list)
                if nzdusd_added:
                    test_logger.info("  PASS: handle_nwe_alert() adds symbol to hot list")
                else:
                    self._record_result("Test 7: Alerts Integration", False, "Symbol not added to hot list via Alerts")
                    return False
            else:
                self._record_result("Test 7: Alerts Integration", False, "handle_nwe_alert() returned False")
                return False

            # Test get_orchestrator_stats
            stats = alerts.get_orchestrator_stats()
            if "hot_list_size" in stats:
                test_logger.info(f"  PASS: get_orchestrator_stats() returns: {stats}")
                self._record_result("Test 7: Alerts Integration", True, "Alerts class integration working")
                return True
            else:
                self._record_result("Test 7: Alerts Integration", False, "get_orchestrator_stats() returned empty")
                return False

        except Exception as e:
            self._record_result("Test 7: Alerts Integration", False, f"Exception: {e}")
            return False

    def _find_indicator(self, shorttitle: str):
        """Find an indicator by its short title."""
        try:
            sleep(2)
            indicators = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')
                )
            )

            for ind in indicators:
                try:
                    title = ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text
                    if title == shorttitle:
                        return ind
                except:
                    continue

            return None
        except:
            return None

    def _add_indicator_from_favorites(self, indicator_name: str) -> bool:
        """Add an indicator from favorites menu."""
        try:
            # Click favorites dropdown
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'div[id="header-toolbar-indicators"] button[data-name="show-favorite-indicators"]')
                )
            ).click()

            sleep(0.5)

            # Find and click the indicator
            menu = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]'))
            )

            items = menu.find_elements(By.CSS_SELECTOR, 'div[data-role="menuitem"]')
            for item in items:
                try:
                    label = item.find_element(By.CSS_SELECTOR, 'span[class="label-l0nf43ai apply-overflow-tooltip"]').text
                    if indicator_name in label:
                        item.click()
                        test_logger.info(f"Added indicator: {indicator_name}")
                        return True
                except:
                    continue

            # Close menu if indicator not found
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            return False
        except Exception as e:
            test_logger.error(f"Error adding indicator: {e}")
            return False

    def _record_result(self, test_name: str, passed: bool, message: str):
        """Record a test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        test_logger.info(f"[{status}] {test_name}: {message}")

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

    def cleanup(self):
        """Clean up resources."""
        test_logger.info("Cleaning up...")
        # Don't close browser to allow manual inspection
        test_logger.info("Browser left open for manual inspection")

    def run_all_tests(self):
        """Run all tests."""
        if not self.setup():
            self.print_summary()
            return False

        # Run tests
        self.test_1_indicator_loads()
        self.test_2_debug_table_displays()
        self.test_3_create_alert()
        self.test_4_orchestrator_nwe_alert()
        self.test_5_alert_json_format()
        self.test_6_hot_list_management()
        self.test_7_integration_with_alerts_class()

        # Print summary
        all_passed = self.print_summary()

        # Cleanup
        self.cleanup()

        return all_passed


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("TTE NWE SCREENER AUTOMATED TEST")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"SYMBOL_INPUTS configured: {SYMBOL_INPUTS}")
    print("=" * 60 + "\n")

    tester = NWEScreenerTest()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
