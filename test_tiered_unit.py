"""
Unit Tests: TTE Tiered Architecture (No Browser Required)

This script tests the Python integration components without requiring
TradingView or Chrome browser:
1. TieredOrchestrator hot list management
2. Alert format detection (NWE vs TTE)
3. JSON parsing
4. Signal level tracking

Usage:
    python test_tiered_unit.py
"""

import unittest
from datetime import datetime, timedelta
from json import loads, dumps
from tiered_orchestrator import TieredOrchestrator, HotSymbol, Tier2Result, SignalDirection


class MockDriver:
    """Mock Selenium WebDriver for testing."""
    pass


class TestTieredOrchestrator(unittest.TestCase):
    """Test TieredOrchestrator hot list management."""

    def setUp(self):
        """Create fresh orchestrator for each test."""
        self.orchestrator = TieredOrchestrator(MockDriver())

    def test_on_nwe_alert_adds_to_hot_list(self):
        """Test that NWE alert adds symbol to hot list."""
        alert = {"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4,D1"}
        self.orchestrator.on_nwe_alert(alert)

        hot_symbols = self.orchestrator.get_hot_symbols()
        self.assertEqual(len(hot_symbols), 1)
        self.assertEqual(hot_symbols[0].symbol, "GBPAUD")
        self.assertEqual(hot_symbols[0].direction, SignalDirection.BULLISH)
        self.assertIn("H4", hot_symbols[0].timeframes)
        self.assertIn("D1", hot_symbols[0].timeframes)

    def test_on_nwe_alert_updates_existing(self):
        """Test that new NWE alert updates existing hot list entry."""
        # Add bullish
        self.orchestrator.on_nwe_alert({"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4"})

        # Update to bearish
        self.orchestrator.on_nwe_alert({"symbol": "GBPAUD", "nwe": "bearish", "tf": "D1"})

        hot_symbols = self.orchestrator.get_hot_symbols()
        self.assertEqual(len(hot_symbols), 1)
        self.assertEqual(hot_symbols[0].direction, SignalDirection.BEARISH)
        self.assertEqual(hot_symbols[0].timeframes, ["D1"])

    def test_on_nwe_alert_multiple_symbols(self):
        """Test adding multiple symbols to hot list."""
        symbols = [
            {"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4"},
            {"symbol": "EURUSD", "nwe": "bearish", "tf": "D1"},
            {"symbol": "USDJPY", "nwe": "bullish", "tf": "H4,D1"},
        ]

        for alert in symbols:
            self.orchestrator.on_nwe_alert(alert)

        hot_symbols = self.orchestrator.get_hot_symbols()
        self.assertEqual(len(hot_symbols), 3)

        symbol_names = [hs.symbol for hs in hot_symbols]
        self.assertIn("GBPAUD", symbol_names)
        self.assertIn("EURUSD", symbol_names)
        self.assertIn("USDJPY", symbol_names)

    def test_remove_from_hot_list(self):
        """Test removing symbol from hot list."""
        self.orchestrator.on_nwe_alert({"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4"})
        self.orchestrator.on_nwe_alert({"symbol": "EURUSD", "nwe": "bearish", "tf": "D1"})

        self.assertEqual(len(self.orchestrator.get_hot_symbols()), 2)

        self.orchestrator.remove_from_hot_list("GBPAUD")

        hot_symbols = self.orchestrator.get_hot_symbols()
        self.assertEqual(len(hot_symbols), 1)
        self.assertEqual(hot_symbols[0].symbol, "EURUSD")

    def test_get_statistics(self):
        """Test statistics calculation."""
        self.orchestrator.on_nwe_alert({"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4"})
        self.orchestrator.on_nwe_alert({"symbol": "EURUSD", "nwe": "bearish", "tf": "D1"})
        self.orchestrator.on_nwe_alert({"symbol": "USDJPY", "nwe": "bullish", "tf": "H4"})

        stats = self.orchestrator.get_statistics()

        self.assertEqual(stats["hot_list_size"], 3)
        self.assertEqual(stats["bullish_count"], 2)
        self.assertEqual(stats["bearish_count"], 1)

    def test_to_json_and_from_json(self):
        """Test JSON export/import of hot list."""
        self.orchestrator.on_nwe_alert({"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4,D1"})
        self.orchestrator.on_nwe_alert({"symbol": "EURUSD", "nwe": "bearish", "tf": "D1"})

        # Export
        json_str = self.orchestrator.to_json()
        self.assertIsNotNone(json_str)

        # Create new orchestrator and import
        new_orchestrator = TieredOrchestrator(MockDriver())
        new_orchestrator.from_json(json_str)

        # Verify
        hot_symbols = new_orchestrator.get_hot_symbols()
        self.assertEqual(len(hot_symbols), 2)

        symbol_names = [hs.symbol for hs in hot_symbols]
        self.assertIn("GBPAUD", symbol_names)
        self.assertIn("EURUSD", symbol_names)


class TestHotSymbol(unittest.TestCase):
    """Test HotSymbol dataclass methods."""

    def test_needs_recheck_true_when_never_checked(self):
        """Test needs_recheck returns True when last_checked is None."""
        hs = HotSymbol(
            symbol="GBPAUD",
            direction=SignalDirection.BULLISH,
            timeframes=["H4"],
            nwe_triggered_at=datetime.now()
        )
        self.assertTrue(hs.needs_recheck())

    def test_needs_recheck_true_after_interval(self):
        """Test needs_recheck returns True after recheck interval."""
        hs = HotSymbol(
            symbol="GBPAUD",
            direction=SignalDirection.BULLISH,
            timeframes=["H4"],
            nwe_triggered_at=datetime.now(),
            last_checked=datetime.now() - timedelta(minutes=65)  # 65 min ago
        )
        self.assertTrue(hs.needs_recheck(recheck_interval_minutes=60))

    def test_needs_recheck_false_within_interval(self):
        """Test needs_recheck returns False within recheck interval."""
        hs = HotSymbol(
            symbol="GBPAUD",
            direction=SignalDirection.BULLISH,
            timeframes=["H4"],
            nwe_triggered_at=datetime.now(),
            last_checked=datetime.now() - timedelta(minutes=30)  # 30 min ago
        )
        self.assertFalse(hs.needs_recheck(recheck_interval_minutes=60))

    def test_is_expired_true(self):
        """Test is_expired returns True after expiry period."""
        hs = HotSymbol(
            symbol="GBPAUD",
            direction=SignalDirection.BULLISH,
            timeframes=["H4"],
            nwe_triggered_at=datetime.now() - timedelta(hours=25)  # 25 hours ago
        )
        self.assertTrue(hs.is_expired(expiry_hours=24))

    def test_is_expired_false(self):
        """Test is_expired returns False within expiry period."""
        hs = HotSymbol(
            symbol="GBPAUD",
            direction=SignalDirection.BULLISH,
            timeframes=["H4"],
            nwe_triggered_at=datetime.now() - timedelta(hours=12)  # 12 hours ago
        )
        self.assertFalse(hs.is_expired(expiry_hours=24))


class TestAlertFormatDetection(unittest.TestCase):
    """Test alert format detection logic."""

    def test_nwe_alert_format(self):
        """Test NWE alert JSON format detection."""
        nwe_alerts = [
            '{"symbol":"GBPAUD","nwe":"bullish","tf":"H4"}',
            '{"symbol":"EURUSD","nwe":"bearish","tf":"H4,D1"}',
            '{"symbol":"USDJPY","nwe":"bullish","tf":"D1"}',
        ]

        for json_str in nwe_alerts:
            parsed = loads(json_str)
            is_nwe = "nwe" in parsed and "symbol" in parsed
            self.assertTrue(is_nwe, f"Should be NWE format: {json_str}")

    def test_tte_screener_alert_format(self):
        """Test TTE Screener alert format (not NWE)."""
        tte_alerts = [
            '{"GBPAUD": {"timeframe": "1H", "entryPrice": "2.1234"}}',
            '{"symbol":"GBPAUD","signal":"BUY","level":3,"details":"NWE:H4 OB:W1 DIV:H4"}',
        ]

        for json_str in tte_alerts:
            parsed = loads(json_str)
            is_nwe = "nwe" in parsed and "symbol" in parsed
            self.assertFalse(is_nwe, f"Should NOT be NWE format: {json_str}")

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        invalid = "not valid json {"

        with self.assertRaises(Exception):
            loads(invalid)


class TestTier2Result(unittest.TestCase):
    """Test Tier2Result dataclass."""

    def test_level_1_nwe_only(self):
        """Test Level 1 signal (NWE only)."""
        result = Tier2Result(
            symbol="GBPAUD",
            direction=SignalDirection.BULLISH,
            ob_found=False,
            signal_level=1
        )
        self.assertEqual(result.signal_level, 1)
        self.assertFalse(result.ob_found)
        self.assertFalse(result.div_found)

    def test_level_2_nwe_plus_ob(self):
        """Test Level 2 signal (NWE + OB)."""
        result = Tier2Result(
            symbol="GBPAUD",
            direction=SignalDirection.BULLISH,
            ob_found=True,
            ob_timeframe="H4",
            ob_type="OB",
            signal_level=2
        )
        self.assertEqual(result.signal_level, 2)
        self.assertTrue(result.ob_found)
        self.assertFalse(result.div_found)

    def test_level_3_full_signal(self):
        """Test Level 3 signal (NWE + OB + DIV)."""
        result = Tier2Result(
            symbol="GBPAUD",
            direction=SignalDirection.BULLISH,
            ob_found=True,
            ob_timeframe="H4",
            ob_type="OB",
            div_found=True,
            div_timeframe="D1",
            div_type="Logic2",
            signal_level=3
        )
        self.assertEqual(result.signal_level, 3)
        self.assertTrue(result.ob_found)
        self.assertTrue(result.div_found)


class TestIntegrationWithAlerts(unittest.TestCase):
    """Test integration points with handle_alerts.py."""

    def test_is_nwe_alert_function(self):
        """Test is_nwe_alert function logic (mimics handle_alerts.py)."""
        def is_nwe_alert(alert_msg: dict) -> bool:
            return "nwe" in alert_msg and "symbol" in alert_msg

        # NWE alerts
        self.assertTrue(is_nwe_alert({"symbol": "GBPAUD", "nwe": "bullish", "tf": "H4"}))
        self.assertTrue(is_nwe_alert({"symbol": "EURUSD", "nwe": "bearish", "tf": "D1"}))

        # Not NWE alerts
        self.assertFalse(is_nwe_alert({"GBPAUD": {"timeframe": "1H"}}))
        self.assertFalse(is_nwe_alert({"symbol": "GBPAUD", "signal": "BUY"}))
        self.assertFalse(is_nwe_alert({}))


def run_tests():
    """Run all unit tests."""
    print("\n" + "=" * 60)
    print("TTE TIERED ARCHITECTURE UNIT TESTS")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTieredOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestHotSymbol))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertFormatDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestTier2Result))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithAlerts))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 60)

    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
