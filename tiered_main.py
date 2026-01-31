"""
TTE Tiered Orchestrator - Entry Point

Entry point for the tiered screening system that rotates through 1000+ symbols
using the Stock Buddy API backend.

Usage:
    python tiered_main.py              # Run orchestrator
    python tiered_main.py --validate   # Validate configuration
    python tiered_main.py --test-api   # Test API connection
    python tiered_main.py --test-browser  # Test browser automation
    python tiered_main.py --stats      # Show current statistics
"""

import sys
import time
import argparse
from config import Config
from utils.logger import logger


def main():
    """Main entry point for the TTE Tiered Orchestrator."""
    parser = argparse.ArgumentParser(
        description='TTE Tiered Orchestrator - 1000+ Symbol Screening System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tiered_main.py              # Run the orchestrator
  python tiered_main.py --validate   # Check configuration
  python tiered_main.py --test-api   # Test Stock Buddy API connection
  python tiered_main.py --test-browser  # Test Chrome browser automation
  python tiered_main.py --stats      # Show current system statistics
        """
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration and exit'
    )

    parser.add_argument(
        '--test-api',
        action='store_true',
        help='Test API connection and exit'
    )

    parser.add_argument(
        '--test-browser',
        action='store_true',
        help='Test browser automation and exit'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show current system statistics and exit'
    )

    parser.add_argument(
        '--config',
        action='store_true',
        help='Print current configuration and exit'
    )

    parser.add_argument(
        '--single-cycle',
        action='store_true',
        help='Run one complete cycle and exit (for testing)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--init',
        action='store_true',
        help='Initialize TTE system (seed symbols and rotation state)'
    )

    parser.add_argument(
        '--init-force',
        action='store_true',
        help='Force reinitialize (clears existing data)'
    )

    args = parser.parse_args()

    # Print banner
    print()
    print("=" * 60)
    print("  TTE Tiered Orchestrator")
    print("  1000+ Symbol Screening System")
    print("=" * 60)
    print()

    # Print configuration if requested
    if args.config:
        Config.print_config()
        sys.exit(0)

    # Enable debug logging if requested
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        print("[DEBUG] Debug logging enabled")

    # Validate configuration
    if args.validate or not any([args.test_api, args.test_browser, args.stats, args.single_cycle, args.init, args.init_force]):
        print("Validating configuration...")
        try:
            Config.validate(strict=True)
            print("[OK] Configuration is valid")
        except ValueError as e:
            print(f"[ERROR] Configuration error: {e}")
            sys.exit(1)

        if args.validate:
            sys.exit(0)

    # Test API connection
    if args.test_api:
        print("\nTesting API connection...")
        from api_client import StockBuddyAPIClient

        client = StockBuddyAPIClient()

        try:
            if client.health_check():
                print(f"[OK] Connected to API at {Config.STOCK_BUDDY_API_URL}")

                print("\nFetching system stats...")
                stats = client.get_stats()

                signals = stats.get('signals', {})
                rotation = stats.get('rotation', {})
                hot_list = stats.get('hot_list', {})

                print(f"  Signals today: {signals.get('today', 0)}")
                print(f"  Total signals: {signals.get('total', 0)}")
                print(f"  Hot list pending: {hot_list.get('pending', 0)}")
                print(f"  Current batch: #{rotation.get('batch_number', 0)}")
                print(f"  Current rotation: #{rotation.get('rotation_number', 0)}")

                print("\n[OK] API test passed")
                sys.exit(0)
            else:
                print("[ERROR] API health check failed")
                sys.exit(1)

        except Exception as e:
            print(f"[ERROR] API test failed: {e}")
            sys.exit(1)

        finally:
            client.close()

    # Test browser automation
    if args.test_browser:
        print("\nTesting browser automation...")
        from selenium_manager import SeleniumManager

        browser = SeleniumManager()

        try:
            print("  Launching Chrome...")
            driver = browser.get_driver()
            print("  [OK] Chrome launched successfully")

            print("  Navigating to TradingView...")
            driver.get("https://www.tradingview.com")
            print("  [OK] Navigation successful")

            print("\n[OK] Browser test passed")
            print("\nPress Enter to close browser...")
            input()

            browser.close()
            sys.exit(0)

        except Exception as e:
            print(f"[ERROR] Browser test failed: {e}")
            browser.close()
            sys.exit(1)

    # Show statistics
    if args.stats:
        print("\nFetching current statistics...")
        from api_client import StockBuddyAPIClient

        client = StockBuddyAPIClient()

        try:
            stats = client.get_stats()

            signals = stats.get('signals', {})
            by_level = stats.get('by_level', {})
            by_direction = stats.get('by_direction', {})
            hot_list = stats.get('hot_list', {})
            rotation = stats.get('rotation', {})

            print("\n--- Signal Statistics ---")
            print(f"  Today:     {signals.get('today', 0)}")
            print(f"  This week: {signals.get('week', 0)}")
            print(f"  This month: {signals.get('month', 0)}")
            print(f"  Total:     {signals.get('total', 0)}")
            print(f"  Pending screenshots: {signals.get('pending_screenshots', 0)}")

            print("\n--- By Level ---")
            print(f"  Level 1 (NWE only):    {by_level.get('level_1', 0)}")
            print(f"  Level 2 (NWE + OB):    {by_level.get('level_2', 0)}")
            print(f"  Level 3 (NWE + OB + DIV): {by_level.get('level_3', 0)}")

            print("\n--- By Direction ---")
            print(f"  Bullish: {by_direction.get('bullish', 0)}")
            print(f"  Bearish: {by_direction.get('bearish', 0)}")

            print("\n--- Hot List ---")
            print(f"  Pending Tier 2: {hot_list.get('pending', 0)}")
            print(f"  Avg age: {hot_list.get('avg_age_minutes', 0)} minutes")

            print("\n--- Symbol Rotation ---")
            print(f"  Current batch: #{rotation.get('batch_number', 0)}")
            print(f"  Current rotation: #{rotation.get('rotation_number', 0)}")
            print(f"  Progress: {rotation.get('progress_percent', 0)}%")
            print(f"  Scanned: {rotation.get('symbols_scanned', 0)}/{rotation.get('total_symbols', 0)}")

            client.close()
            sys.exit(0)

        except Exception as e:
            print(f"[ERROR] Failed to fetch stats: {e}")
            client.close()
            sys.exit(1)

    # Initialize TTE system
    if args.init or args.init_force:
        print("\nInitializing TTE rotation state...")
        import requests
        
        init_url = Config.STOCK_BUDDY_API_URL.replace('/tte', '') + '/tte/init'
        print(f"Calling: {init_url}")
        
        try:
            response = requests.post(
                init_url,
                json={'force': args.init_force},
                timeout=30
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                result = data.get('data', {})
                symbols_info = result.get('symbols', {})
                rotation_info = result.get('rotation_state', {})
                
                print(f"\n[OK] TTE rotation state initialized!")
                print(f"\nSymbols in database: {symbols_info.get('total', 0)}")
                
                counts = symbols_info.get('counts', {})
                if counts:
                    print(f"  Priority A (every rotation): {counts.get('A', 0)}")
                    print(f"  Priority B (every 3rd): {counts.get('B', 0)}")
                    print(f"  Priority C (every 10th): {counts.get('C', 0)}")
                
                print(f"\nRotation state:")
                print(f"  Batch #: {rotation_info.get('batch_number', 0)}")
                print(f"  Rotation #: {rotation_info.get('rotation_number', 0)}")
                
                print("\nYou can now run: python tiered_main.py --single-cycle")
                sys.exit(0)
            else:
                error = data.get('error', 'Unknown error')
                code = data.get('code', '')
                
                if code == 'ALREADY_INITIALIZED':
                    print(f"\n[INFO] {error}")
                    print("Use --init-force to reset rotation state")
                elif code == 'NO_SYMBOLS':
                    print(f"\n[WARN] {error}")
                    print("The tte_symbols collection is empty.")
                else:
                    print(f"\n[ERROR] Initialization failed: {error}")
                sys.exit(1)
                
        except requests.exceptions.RequestException as e:
            print(f"\n[ERROR] Request failed: {e}")
            sys.exit(1)

    # Run single cycle (for testing)
    if args.single_cycle:
        print("\nRunning single cycle test...")
        print("This will run one complete orchestration cycle and exit.")
        print()
        
        from orchestrator import TieredOrchestrator, OrchestratorError
        
        orchestrator = TieredOrchestrator()
        
        try:
            # Initialize
            print("Checking API connectivity...")
            from api_client import StockBuddyAPIClient
            api = StockBuddyAPIClient()
            
            if not api.health_check():
                print("[ERROR] API health check failed")
                sys.exit(1)
            print("[OK] API is healthy")
            
            # Get stats
            stats = api.get_stats()
            rotation = stats.get('rotation', {})
            print(f"Current state: Batch #{rotation.get('batch_number', 0)}, Rotation #{rotation.get('rotation_number', 0)}")
            print()
            
            # Initialize browser
            print("Initializing browser...")
            from selenium_manager import SeleniumManager
            browser = SeleniumManager()
            driver = browser.get_driver()
            print("[OK] Browser ready")
            print()
            
            # Phase 1: NWE Batch
            print("=" * 50)
            print("Phase 1: NWE Batch Rotation")
            print("=" * 50)
            
            batch_response = api.get_next_symbol_batch(size=Config.NWE_BATCH_SIZE)
            if batch_response.get('success'):
                batch = batch_response.get('batch', [])
                symbols = [s['symbol'] for s in batch]
                
                print(f"Got {len(symbols)} symbols for NWE scan")
                if symbols:
                    print(f"Symbols: {', '.join(symbols[:5])}..." if len(symbols) > 5 else f"Symbols: {', '.join(symbols)}")
                    
                    print(f"\nUpdating NWE screener with {len(symbols)} symbols...")
                    browser.update_nwe_symbols(symbols)
                    print("[OK] NWE screener updated with symbols and alert created")

                    print(f"\nWaiting {Config.NWE_BATCH_WAIT}s for NWE scan...")
                    time.sleep(Config.NWE_BATCH_WAIT)
                    print("[OK] NWE scan wait complete")
                    
                    # Mark as scanned
                    api.mark_symbols_scanned(symbols)
                    print(f"[OK] Marked {len(symbols)} symbols as scanned")
            else:
                print("[WARN] Could not get symbol batch - rotation may need initialization")
            
            print()
            
            # Phase 2: OBDIV Processing
            print("=" * 50)
            print("Phase 2: OBDIV Hot Symbol Processing")
            print("=" * 50)
            
            hot_symbols = api.get_hot_symbols(limit=Config.OBDIV_BATCH_SIZE)
            if hot_symbols:
                symbols = [s['symbol'] for s in hot_symbols]
                print(f"Got {len(symbols)} hot symbols: {', '.join(symbols)}")
                
                print(f"\nUpdating OBDIV screener with {len(symbols)} symbols...")
                browser.update_obdiv_symbols(symbols)
                print("[OK] OBDIV screener updated with symbols and alert created")

                print(f"\nWaiting {Config.OBDIV_BATCH_WAIT}s for OBDIV scan...")
                time.sleep(Config.OBDIV_BATCH_WAIT)
                print("[OK] OBDIV scan wait complete")
            else:
                print("[INFO] No hot symbols pending OBDIV check")
            
            print()
            
            # Phase 3: Screenshots
            print("=" * 50)
            print("Phase 3: Screenshot Capture")
            print("=" * 50)
            
            pending = api.get_pending_screenshots(limit=Config.SCREENSHOT_BATCH_SIZE)
            if pending:
                print(f"Got {len(pending)} signals pending screenshots")
                for signal in pending[:2]:  # Only do 2 for testing
                    symbol = signal.get('symbol', 'UNKNOWN')
                    print(f"  Would capture screenshot for: {symbol}")
            else:
                print("[INFO] No signals pending screenshots")
            
            print()
            print("=" * 50)
            print("Single Cycle Test Complete!")
            print("=" * 50)
            print()
            print("The orchestrator is working correctly.")
            print("To run continuously: python tiered_main.py")
            print()
            
            print("Press Enter to close browser...")
            input()
            
            browser.close()
            api.close()
            sys.exit(0)
            
        except Exception as e:
            print(f"\n[ERROR] Single cycle failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # Run orchestrator
    print("\nStarting orchestrator...")
    print("Press Ctrl+C to stop\n")

    from orchestrator import TieredOrchestrator, OrchestratorError

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
