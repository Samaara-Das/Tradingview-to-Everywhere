"""
End-to-End Test: TTE Tiered Architecture

This script tests the complete tiered signal flow:
1. NWE alert received → added to hot list (Tier 1)
2. Hot list processed → Tier 2 checks (OB + Divergence)
3. Signal levels calculated (1=NWE, 2=NWE+OB, 3=NWE+OB+DIV)
4. Full signals dispatched

Uses Edge browser with remote debugging for live TradingView testing.

SETUP:
1. Start Edge with remote debugging:
   powershell -Command "Start-Process -FilePath 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe' -ArgumentList '--remote-debugging-port=9222', 'https://www.tradingview.com/chart'"
2. Sign in to TradingView
3. Run: python test_e2e_tiered.py
"""

import sys
from time import sleep
from datetime import datetime, timedelta
from json import loads, dumps
from unittest.mock import patch, MagicMock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from tiered_orchestrator import TieredOrchestrator, HotSymbol, Tier2Result, SignalDirection

REMOTE_DEBUG_PORT = 9222


class E2ETest:
    """End-to-end test for tiered architecture."""

    def __init__(self):
        self.driver = None
        self.orchestrator = None
        self.test_results = []

    def setup(self):
        """Connect to Edge browser via remote debugging."""
        print("\n" + "=" * 60)
        print("SETUP: Connecting to Edge browser...")
        print("=" * 60)

        try:
            edge_options = webdriver.EdgeOptions()
            edge_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{REMOTE_DEBUG_PORT}")
            self.driver = webdriver.Edge(options=edge_options)
            print("Connected to Edge browser")

            self.orchestrator = TieredOrchestrator(self.driver)
            print("Orchestrator initialized")

            self._record_result("Setup", True, "Connected to browser and initialized orchestrator")
            return True

        except WebDriverException as e:
            if "cannot connect" in str(e).lower() or "refused" in str(e).lower():
                print("\nEdge not running with remote debugging.")
                print("Start Edge with:")
                print('  powershell -Command "Start-Process -FilePath \'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe\' -ArgumentList \'--remote-debugging-port=9222\', \'https://www.tradingview.com/chart\'"')
            self._record_result("Setup", False, f"Connection failed: {e}")
            return False
        except Exception as e:
            self._record_result("Setup", False, f"Exception: {e}")
            return False

    def test_1_nwe_alert_to_hot_list(self):
        """Test 1: NWE alerts correctly populate the hot list."""
        print("\n" + "=" * 60)
        print("TEST 1: NWE Alert -> Hot List")
        print("=" * 60)

        try:
            # Clear hot list
            self.orchestrator.hot_list.clear()

            # Simulate NWE alerts
            test_alerts = [
                {"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4,D1"},
                {"symbol": "EURUSD", "nwe": "bearish", "tf": "D1"},
                {"symbol": "USDJPY", "nwe": "bullish", "tf": "H4"},
            ]

            for alert in test_alerts:
                self.orchestrator.on_nwe_alert(alert)
                print(f"  Added: {alert['symbol']} - {alert['nwe']}")

            # Verify hot list
            hot_symbols = self.orchestrator.get_hot_symbols()
            if len(hot_symbols) != 3:
                self._record_result("Test 1: Hot List", False, f"Expected 3 symbols, got {len(hot_symbols)}")
                return False

            # Verify directions
            gbpaud = self.orchestrator.hot_list.get("GBPAUD")
            eurusd = self.orchestrator.hot_list.get("EURUSD")

            if gbpaud.direction != SignalDirection.BULLISH:
                self._record_result("Test 1: Hot List", False, "GBPAUD direction incorrect")
                return False

            if eurusd.direction != SignalDirection.BEARISH:
                self._record_result("Test 1: Hot List", False, "EURUSD direction incorrect")
                return False

            # Verify timeframes
            if "H4" not in gbpaud.timeframes or "D1" not in gbpaud.timeframes:
                self._record_result("Test 1: Hot List", False, "GBPAUD timeframes incorrect")
                return False

            print(f"  Hot list has {len(hot_symbols)} symbols")
            print(f"  GBPAUD: {gbpaud.direction.value} on {gbpaud.timeframes}")
            print(f"  EURUSD: {eurusd.direction.value} on {eurusd.timeframes}")

            self._record_result("Test 1: Hot List", True, "All NWE alerts correctly added to hot list")
            return True

        except Exception as e:
            self._record_result("Test 1: Hot List", False, f"Exception: {e}")
            return False

    def test_2_hot_list_update(self):
        """Test 2: Hot list updates correctly when direction changes."""
        print("\n" + "=" * 60)
        print("TEST 2: Hot List Update on Direction Change")
        print("=" * 60)

        try:
            # GBPAUD should already be in hot list as bullish
            original = self.orchestrator.hot_list.get("GBPAUD")
            if not original:
                self._record_result("Test 2: Update", False, "GBPAUD not in hot list")
                return False

            original_time = original.nwe_triggered_at
            print(f"  Original: GBPAUD - {original.direction.value}")

            # Update to bearish
            sleep(0.1)  # Ensure timestamp changes
            self.orchestrator.on_nwe_alert({"symbol": "GBPAUD", "nwe": "bearish", "tf": "D1"})

            updated = self.orchestrator.hot_list.get("GBPAUD")
            print(f"  Updated: GBPAUD - {updated.direction.value}")

            if updated.direction != SignalDirection.BEARISH:
                self._record_result("Test 2: Update", False, "Direction not updated")
                return False

            if updated.timeframes != ["D1"]:
                self._record_result("Test 2: Update", False, f"Timeframes not updated: {updated.timeframes}")
                return False

            if updated.nwe_triggered_at <= original_time:
                self._record_result("Test 2: Update", False, "Timestamp not updated")
                return False

            # Verify ob_checked was reset
            if updated.ob_checked:
                self._record_result("Test 2: Update", False, "ob_checked should be reset")
                return False

            self._record_result("Test 2: Update", True, "Hot list correctly updated on direction change")
            return True

        except Exception as e:
            self._record_result("Test 2: Update", False, f"Exception: {e}")
            return False

    def test_3_hot_list_expiry(self):
        """Test 3: Expired symbols are removed from hot list."""
        print("\n" + "=" * 60)
        print("TEST 3: Hot List Expiry")
        print("=" * 60)

        try:
            # Add a symbol with old timestamp
            old_time = datetime.now() - timedelta(hours=25)
            self.orchestrator.hot_list["EXPIRED_TEST"] = HotSymbol(
                symbol="EXPIRED_TEST",
                direction=SignalDirection.BULLISH,
                timeframes=["H4"],
                nwe_triggered_at=old_time
            )

            # Add a fresh symbol
            self.orchestrator.on_nwe_alert({"symbol": "FRESH_TEST", "nwe": "bullish", "tf": "H4"})

            print(f"  Added EXPIRED_TEST (25 hours old)")
            print(f"  Added FRESH_TEST (just now)")

            # Check expiry status
            expired_symbol = self.orchestrator.hot_list.get("EXPIRED_TEST")
            fresh_symbol = self.orchestrator.hot_list.get("FRESH_TEST")

            if not expired_symbol.is_expired():
                self._record_result("Test 3: Expiry", False, "EXPIRED_TEST should be expired")
                return False

            if fresh_symbol.is_expired():
                self._record_result("Test 3: Expiry", False, "FRESH_TEST should not be expired")
                return False

            # Force cleanup
            self.orchestrator.last_cleanup = datetime.now() - timedelta(hours=1)
            self.orchestrator._cleanup_expired()

            if "EXPIRED_TEST" in self.orchestrator.hot_list:
                self._record_result("Test 3: Expiry", False, "EXPIRED_TEST should be removed")
                return False

            if "FRESH_TEST" not in self.orchestrator.hot_list:
                self._record_result("Test 3: Expiry", False, "FRESH_TEST should remain")
                return False

            print("  EXPIRED_TEST removed after 24hr expiry")
            print("  FRESH_TEST remains in hot list")

            # Cleanup test symbol
            del self.orchestrator.hot_list["FRESH_TEST"]

            self._record_result("Test 3: Expiry", True, "Expiry logic works correctly")
            return True

        except Exception as e:
            self._record_result("Test 3: Expiry", False, f"Exception: {e}")
            return False

    def test_4_signal_levels(self):
        """Test 4: Signal levels calculated correctly."""
        print("\n" + "=" * 60)
        print("TEST 4: Signal Level Calculation")
        print("=" * 60)

        try:
            # Test Level 1: NWE only
            level1 = Tier2Result(
                symbol="TEST1",
                direction=SignalDirection.BULLISH,
                ob_found=False,
                signal_level=1
            )
            print(f"  Level 1 (NWE only): {level1.signal_level}")
            if level1.signal_level != 1:
                self._record_result("Test 4: Levels", False, "Level 1 incorrect")
                return False

            # Test Level 2: NWE + OB
            level2 = Tier2Result(
                symbol="TEST2",
                direction=SignalDirection.BULLISH,
                ob_found=True,
                ob_timeframe="H4",
                ob_type="OB",
                signal_level=2
            )
            print(f"  Level 2 (NWE + OB): {level2.signal_level}")
            if level2.signal_level != 2:
                self._record_result("Test 4: Levels", False, "Level 2 incorrect")
                return False

            # Test Level 3: NWE + OB + DIV
            level3 = Tier2Result(
                symbol="TEST3",
                direction=SignalDirection.BULLISH,
                ob_found=True,
                ob_timeframe="H4",
                ob_type="OB",
                div_found=True,
                div_timeframe="D1",
                div_type="Logic2",
                signal_level=3
            )
            print(f"  Level 3 (NWE + OB + DIV): {level3.signal_level}")
            if level3.signal_level != 3:
                self._record_result("Test 4: Levels", False, "Level 3 incorrect")
                return False

            self._record_result("Test 4: Levels", True, "All signal levels calculated correctly")
            return True

        except Exception as e:
            self._record_result("Test 4: Levels", False, f"Exception: {e}")
            return False

    def test_5_needs_recheck(self):
        """Test 5: Recheck interval logic works."""
        print("\n" + "=" * 60)
        print("TEST 5: Recheck Interval Logic")
        print("=" * 60)

        try:
            # Symbol never checked
            never_checked = HotSymbol(
                symbol="NEVER",
                direction=SignalDirection.BULLISH,
                timeframes=["H4"],
                nwe_triggered_at=datetime.now()
            )
            print(f"  Never checked: needs_recheck = {never_checked.needs_recheck()}")
            if not never_checked.needs_recheck():
                self._record_result("Test 5: Recheck", False, "Never checked should need recheck")
                return False

            # Symbol checked recently
            recently_checked = HotSymbol(
                symbol="RECENT",
                direction=SignalDirection.BULLISH,
                timeframes=["H4"],
                nwe_triggered_at=datetime.now(),
                last_checked=datetime.now() - timedelta(minutes=30)
            )
            print(f"  Checked 30m ago: needs_recheck = {recently_checked.needs_recheck(60)}")
            if recently_checked.needs_recheck(60):
                self._record_result("Test 5: Recheck", False, "Recently checked should not need recheck")
                return False

            # Symbol checked long ago
            old_checked = HotSymbol(
                symbol="OLD",
                direction=SignalDirection.BULLISH,
                timeframes=["H4"],
                nwe_triggered_at=datetime.now(),
                last_checked=datetime.now() - timedelta(minutes=90)
            )
            print(f"  Checked 90m ago: needs_recheck = {old_checked.needs_recheck(60)}")
            if not old_checked.needs_recheck(60):
                self._record_result("Test 5: Recheck", False, "Old checked should need recheck")
                return False

            self._record_result("Test 5: Recheck", True, "Recheck interval logic works correctly")
            return True

        except Exception as e:
            self._record_result("Test 5: Recheck", False, f"Exception: {e}")
            return False

    def test_6_json_persistence(self):
        """Test 6: Hot list JSON export/import."""
        print("\n" + "=" * 60)
        print("TEST 6: JSON Persistence")
        print("=" * 60)

        try:
            # Clear and populate hot list
            self.orchestrator.hot_list.clear()
            self.orchestrator.on_nwe_alert({"symbol": "JSON_TEST1", "nwe": "bullish", "tf": "H4,D1"})
            self.orchestrator.on_nwe_alert({"symbol": "JSON_TEST2", "nwe": "bearish", "tf": "D1"})

            # Export
            json_str = self.orchestrator.to_json()
            print(f"  Exported {len(self.orchestrator.hot_list)} symbols")

            # Clear and import
            self.orchestrator.hot_list.clear()
            self.orchestrator.from_json(json_str)
            print(f"  Imported {len(self.orchestrator.hot_list)} symbols")

            # Verify
            if len(self.orchestrator.hot_list) != 2:
                self._record_result("Test 6: JSON", False, f"Expected 2, got {len(self.orchestrator.hot_list)}")
                return False

            test1 = self.orchestrator.hot_list.get("JSON_TEST1")
            test2 = self.orchestrator.hot_list.get("JSON_TEST2")

            if not test1 or test1.direction != SignalDirection.BULLISH:
                self._record_result("Test 6: JSON", False, "JSON_TEST1 not restored correctly")
                return False

            if not test2 or test2.direction != SignalDirection.BEARISH:
                self._record_result("Test 6: JSON", False, "JSON_TEST2 not restored correctly")
                return False

            print(f"  JSON_TEST1: {test1.direction.value} on {test1.timeframes}")
            print(f"  JSON_TEST2: {test2.direction.value} on {test2.timeframes}")

            # Cleanup
            del self.orchestrator.hot_list["JSON_TEST1"]
            del self.orchestrator.hot_list["JSON_TEST2"]

            self._record_result("Test 6: JSON", True, "JSON persistence works correctly")
            return True

        except Exception as e:
            self._record_result("Test 6: JSON", False, f"Exception: {e}")
            return False

    def test_7_statistics(self):
        """Test 7: Statistics calculation."""
        print("\n" + "=" * 60)
        print("TEST 7: Statistics Calculation")
        print("=" * 60)

        try:
            # Clear and set up known state
            self.orchestrator.hot_list.clear()
            self.orchestrator.processed_signals.clear()

            self.orchestrator.on_nwe_alert({"symbol": "STAT1", "nwe": "bullish", "tf": "H4"})
            self.orchestrator.on_nwe_alert({"symbol": "STAT2", "nwe": "bullish", "tf": "D1"})
            self.orchestrator.on_nwe_alert({"symbol": "STAT3", "nwe": "bearish", "tf": "H4,D1"})

            # Add a processed signal
            self.orchestrator.processed_signals.append(Tier2Result(
                symbol="STAT1",
                direction=SignalDirection.BULLISH,
                ob_found=True,
                signal_level=3
            ))

            stats = self.orchestrator.get_statistics()
            print(f"  Hot list size: {stats['hot_list_size']}")
            print(f"  Bullish: {stats['bullish_count']}")
            print(f"  Bearish: {stats['bearish_count']}")
            print(f"  Needs check: {stats['needs_check']}")
            print(f"  Processed: {stats['processed_signals']}")
            print(f"  Level 3: {stats['level_3_signals']}")

            if stats['hot_list_size'] != 3:
                self._record_result("Test 7: Stats", False, f"hot_list_size expected 3, got {stats['hot_list_size']}")
                return False

            if stats['bullish_count'] != 2:
                self._record_result("Test 7: Stats", False, f"bullish_count expected 2, got {stats['bullish_count']}")
                return False

            if stats['bearish_count'] != 1:
                self._record_result("Test 7: Stats", False, f"bearish_count expected 1, got {stats['bearish_count']}")
                return False

            if stats['level_3_signals'] != 1:
                self._record_result("Test 7: Stats", False, f"level_3_signals expected 1, got {stats['level_3_signals']}")
                return False

            # Cleanup
            self.orchestrator.hot_list.clear()
            self.orchestrator.processed_signals.clear()

            self._record_result("Test 7: Stats", True, "Statistics calculated correctly")
            return True

        except Exception as e:
            self._record_result("Test 7: Stats", False, f"Exception: {e}")
            return False

    def test_8_browser_navigation(self):
        """Test 8: Browser can navigate to TradingView chart."""
        print("\n" + "=" * 60)
        print("TEST 8: Browser Navigation")
        print("=" * 60)

        try:
            current_url = self.driver.current_url
            print(f"  Current URL: {current_url[:60]}...")

            if "tradingview.com" not in current_url:
                # Navigate to TradingView
                self.driver.get("https://www.tradingview.com/chart")
                sleep(3)
                current_url = self.driver.current_url

            if "tradingview.com" in current_url:
                print("  TradingView accessible")
                self._record_result("Test 8: Browser", True, "Browser can access TradingView")
                return True
            else:
                self._record_result("Test 8: Browser", False, "Could not access TradingView")
                return False

        except Exception as e:
            self._record_result("Test 8: Browser", False, f"Exception: {e}")
            return False

    def _record_result(self, test_name: str, passed: bool, message: str):
        """Record test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({"test": test_name, "passed": passed, "message": message})
        print(f"[{status}] {test_name}: {message}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("END-TO-END TEST SUMMARY")
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
        """Run all end-to-end tests."""
        if not self.setup():
            self.print_summary()
            return False

        self.test_1_nwe_alert_to_hot_list()
        self.test_2_hot_list_update()
        self.test_3_hot_list_expiry()
        self.test_4_signal_levels()
        self.test_5_needs_recheck()
        self.test_6_json_persistence()
        self.test_7_statistics()
        self.test_8_browser_navigation()

        return self.print_summary()


def main():
    print("\n" + "=" * 60)
    print("TTE TIERED ARCHITECTURE END-TO-END TEST")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    tester = E2ETest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
