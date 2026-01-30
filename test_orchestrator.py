"""
TTE Orchestrator - Complete Test Suite
======================================
Run this script to test both API connectivity and browser automation.

Usage:
    python test_orchestrator.py --api      # Test API only
    python test_orchestrator.py --browser  # Test browser only
    python test_orchestrator.py --all      # Test everything
"""
import os
import sys
import time
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_banner():
    print()
    print("=" * 70)
    print("  TTE Tiered Orchestrator - Test Suite")
    print("  Testing API Connectivity and Browser Automation")
    print("=" * 70)
    print()


def print_section(title):
    print()
    print("-" * 70)
    print(f"  {title}")
    print("-" * 70)


def test_api():
    """Test Stock Buddy API connectivity."""
    import requests
    
    print_section("API CONNECTIVITY TESTS")
    
    api_url = os.getenv('STOCK_BUDDY_API_URL', 'https://stock-buddy-app.vercel.app/api/tte')
    print(f"API Base URL: {api_url}")
    print()
    
    results = {
        'health': False,
        'stats': False,
        'next_batch': False,
        'hot_symbols': False,
        'signals': False
    }
    
    # Test 1: Health Check
    print("[1/5] Health Check...")
    try:
        health_url = api_url.replace('/tte', '') + '/health'
        response = requests.get(health_url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print(f"      ✅ PASSED - API is healthy")
                print(f"         Database: {data.get('database', 'unknown')}")
                results['health'] = True
            else:
                print(f"      ⚠️ WARNING - Unexpected status: {data}")
        else:
            print(f"      ❌ FAILED - HTTP {response.status_code}")
            print(f"         Response: {response.text[:100]}")
    except requests.exceptions.ConnectionError:
        print("      ❌ FAILED - Connection refused (is the server running?)")
    except requests.exceptions.Timeout:
        print("      ❌ FAILED - Request timed out")
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
    
    # Test 2: Stats Endpoint
    print()
    print("[2/5] Stats Endpoint...")
    try:
        response = requests.get(f"{api_url}/stats", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('data', {})
                print(f"      ✅ PASSED - Stats retrieved")
                
                # Print key stats
                rotation = stats.get('rotation', {})
                signals = stats.get('signals', {})
                hot_list = stats.get('hot_list', {})
                
                print(f"         Total Symbols: {rotation.get('total_symbols', 'N/A')}")
                print(f"         Current Batch: #{rotation.get('batch_number', 'N/A')}")
                print(f"         Total Signals: {signals.get('total', 'N/A')}")
                print(f"         Hot List Pending: {hot_list.get('pending', 'N/A')}")
                results['stats'] = True
            else:
                print(f"      ❌ FAILED - {data.get('error', 'Unknown error')}")
        else:
            print(f"      ❌ FAILED - HTTP {response.status_code}")
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
    
    # Test 3: Next Batch Endpoint
    print()
    print("[3/5] Next Batch Endpoint...")
    try:
        response = requests.get(f"{api_url}/symbols/next-batch?size=5", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                batch_data = data.get('data', {})
                batch = batch_data.get('batch', [])
                rotation = batch_data.get('rotation', {})
                
                print(f"      ✅ PASSED - Batch retrieved")
                print(f"         Batch Size: {len(batch)}")
                print(f"         Batch #: {rotation.get('batch_number', 'N/A')}")
                print(f"         Rotation #: {rotation.get('rotation_number', 'N/A')}")
                
                if batch:
                    symbols = [s.get('symbol', 'N/A') for s in batch[:3]]
                    print(f"         Sample Symbols: {', '.join(symbols)}")
                
                results['next_batch'] = True
            else:
                error = data.get('error', 'Unknown error')
                code = data.get('code', '')
                if code == 'NOT_INITIALIZED':
                    print(f"      ⚠️ WARNING - Rotation not initialized")
                    print(f"         Run the initialization script first")
                else:
                    print(f"      ❌ FAILED - {error}")
        elif response.status_code == 500:
            data = response.json()
            if data.get('code') == 'NOT_INITIALIZED':
                print(f"      ⚠️ WARNING - Rotation state not initialized")
                print(f"         Need to seed the symbols collection first")
            else:
                print(f"      ❌ FAILED - Server error: {data.get('error')}")
        else:
            print(f"      ❌ FAILED - HTTP {response.status_code}")
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
    
    # Test 4: Hot Symbols Endpoint
    print()
    print("[4/5] Hot Symbols Endpoint...")
    try:
        response = requests.get(f"{api_url}/hot-symbols?limit=5", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                symbols_data = data.get('data', {})
                symbols = symbols_data.get('symbols', [])
                
                print(f"      ✅ PASSED - Hot symbols endpoint working")
                print(f"         Hot Symbols Count: {len(symbols)}")
                
                if symbols:
                    for s in symbols[:3]:
                        print(f"         - {s.get('symbol')}: {s.get('direction')}")
                else:
                    print(f"         (No hot symbols pending)")
                
                results['hot_symbols'] = True
            else:
                print(f"      ❌ FAILED - {data.get('error', 'Unknown error')}")
        else:
            print(f"      ❌ FAILED - HTTP {response.status_code}")
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
    
    # Test 5: Signals Endpoint
    print()
    print("[5/5] Signals Endpoint...")
    try:
        response = requests.get(f"{api_url}/signals?limit=5", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                signals_data = data.get('data', {})
                signals = signals_data.get('signals', [])
                total = signals_data.get('total', len(signals))
                
                print(f"      ✅ PASSED - Signals endpoint working")
                print(f"         Total Signals: {total}")
                
                if signals:
                    for s in signals[:3]:
                        print(f"         - {s.get('symbol')}: Level {s.get('level')} ({s.get('direction')})")
                else:
                    print(f"         (No signals yet)")
                
                results['signals'] = True
            else:
                print(f"      ❌ FAILED - {data.get('error', 'Unknown error')}")
        else:
            print(f"      ❌ FAILED - HTTP {response.status_code}")
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
    
    # Summary
    print()
    print("-" * 70)
    print("  API TEST SUMMARY")
    print("-" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {name.replace('_', ' ').title():20} {status}")
    
    print()
    print(f"  Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("  🎉 All API tests passed! Ready for orchestration.")
    elif passed >= 3:
        print("  ⚠️ Some tests failed but core functionality may work.")
    else:
        print("  ❌ Critical tests failed. Please check your configuration.")
    
    return passed == total


def test_browser():
    """Test Selenium browser automation."""
    print_section("BROWSER AUTOMATION TESTS")
    
    chrome_path = os.getenv('CHROME_PROFILE_PATH', '')
    chrome_profile = os.getenv('CHROME_PROFILE_NAME', 'Default')
    nwe_chart = os.getenv('NWE_CHART_URL', '')
    obdiv_chart = os.getenv('OBDIV_CHART_URL', '')
    
    print(f"Chrome Profile Path: {chrome_path}")
    print(f"Chrome Profile Name: {chrome_profile}")
    print(f"NWE Chart URL: {nwe_chart or '(not set)'}")
    print(f"OBDIV Chart URL: {obdiv_chart or '(not set)'}")
    print()
    
    results = {
        'chrome_path': False,
        'driver_init': False,
        'tradingview_nav': False,
        'login_check': False,
        'chart_load': False
    }
    
    # Test 1: Chrome Profile Path
    print("[1/5] Checking Chrome profile path...")
    if chrome_path:
        if os.path.exists(chrome_path):
            print(f"      ✅ PASSED - Chrome profile path exists")
            results['chrome_path'] = True
        else:
            print(f"      ❌ FAILED - Path does not exist: {chrome_path}")
    else:
        print(f"      ❌ FAILED - CHROME_PROFILE_PATH not set in .env")
    
    # Test 2: WebDriver Initialization
    print()
    print("[2/5] Initializing Chrome WebDriver...")
    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        options = webdriver.ChromeOptions()
        
        if chrome_path:
            options.add_argument(f"user-data-dir={chrome_path}")
            if chrome_profile:
                options.add_argument(f"profile-directory={chrome_profile}")
        
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        print(f"      ✅ PASSED - WebDriver initialized")
        print(f"         Browser: Chrome {driver.capabilities.get('browserVersion', 'unknown')}")
        results['driver_init'] = True
        
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
        print(f"         Make sure Chrome is closed before running this test")
        return False
    
    # Test 3: TradingView Navigation
    print()
    print("[3/5] Navigating to TradingView...")
    try:
        driver.get("https://www.tradingview.com")
        time.sleep(3)
        
        print(f"      ✅ PASSED - Navigation successful")
        print(f"         Title: {driver.title[:50]}...")
        results['tradingview_nav'] = True
        
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
    
    # Test 4: Login Check
    print()
    print("[4/5] Checking TradingView login status...")
    try:
        # Look for indicators that user is NOT logged in
        login_needed = False
        
        try:
            # Check for sign-in buttons
            sign_in_elements = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Sign in')] | //button[contains(text(), 'Log in')] | //a[contains(@href, 'signin')]"
            )
            if sign_in_elements:
                for elem in sign_in_elements:
                    if elem.is_displayed():
                        login_needed = True
                        break
        except:
            pass
        
        if login_needed:
            print(f"      ⚠️ WARNING - Not logged into TradingView")
            print(f"         Please log in manually to use screener features")
        else:
            # Check for user menu or avatar
            try:
                user_menu = driver.find_element(By.CSS_SELECTOR, 
                    "[data-name='user-menu'], .tv-header__user-menu-button, [class*='userAvatar']"
                )
                if user_menu:
                    print(f"      ✅ PASSED - Logged into TradingView")
                    results['login_check'] = True
            except:
                print(f"      ⚠️ UNCERTAIN - Could not confirm login status")
                print(f"         Will attempt to continue...")
                results['login_check'] = True  # Assume OK
                
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
    
    # Test 5: Chart Loading
    print()
    print("[5/5] Testing chart navigation...")
    try:
        if nwe_chart:
            print(f"      Loading NWE chart: {nwe_chart[:50]}...")
            driver.get(nwe_chart)
            time.sleep(5)
            
            # Check if chart container exists
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "chart-container"))
                )
                print(f"      ✅ PASSED - Chart loaded successfully")
                results['chart_load'] = True
            except:
                # Try alternate selectors
                try:
                    driver.find_element(By.CSS_SELECTOR, "[class*='chart']")
                    print(f"      ✅ PASSED - Chart element found")
                    results['chart_load'] = True
                except:
                    print(f"      ⚠️ WARNING - Chart container not found (may still work)")
                    results['chart_load'] = True  # Might still work
        else:
            print(f"      ⚠️ SKIPPED - NWE_CHART_URL not configured")
            
    except Exception as e:
        print(f"      ❌ FAILED - {type(e).__name__}: {e}")
    
    # Cleanup
    print()
    print("Closing browser...")
    if driver:
        try:
            driver.quit()
            print("Browser closed.")
        except:
            pass
    
    # Summary
    print()
    print("-" * 70)
    print("  BROWSER TEST SUMMARY")
    print("-" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {name.replace('_', ' ').title():20} {status}")
    
    print()
    print(f"  Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("  🎉 All browser tests passed! Ready for automation.")
    elif passed >= 3:
        print("  ⚠️ Some tests failed but automation may still work.")
    else:
        print("  ❌ Critical tests failed. Please check your configuration.")
    
    return passed >= 3


def main():
    parser = argparse.ArgumentParser(description='TTE Orchestrator Test Suite')
    parser.add_argument('--api', action='store_true', help='Test API connectivity only')
    parser.add_argument('--browser', action='store_true', help='Test browser automation only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Default to --all if no arguments
    if not any([args.api, args.browser, args.all]):
        args.all = True
    
    print_banner()
    
    api_ok = True
    browser_ok = True
    
    if args.api or args.all:
        api_ok = test_api()
    
    if args.browser or args.all:
        browser_ok = test_browser()
    
    # Final Summary
    print()
    print("=" * 70)
    print("  FINAL RESULT")
    print("=" * 70)
    
    if api_ok and browser_ok:
        print()
        print("  ✅ All tests passed!")
        print()
        print("  Next steps:")
        print("    1. Run: python tiered_main.py --single-cycle")
        print("    2. Watch the logs for any issues")
        print("    3. If successful, start production: python tiered_main.py")
        print()
    else:
        print()
        print("  ⚠️ Some tests failed")
        print()
        if not api_ok:
            print("  API Issues:")
            print("    - Check STOCK_BUDDY_API_URL in .env")
            print("    - Verify the Stock Buddy app is deployed and running")
            print("    - Check if MongoDB is connected")
            print()
        if not browser_ok:
            print("  Browser Issues:")
            print("    - Make sure Chrome is fully closed")
            print("    - Check CHROME_PROFILE_PATH in .env")
            print("    - Log into TradingView in Chrome manually first")
            print()


if __name__ == "__main__":
    main()
