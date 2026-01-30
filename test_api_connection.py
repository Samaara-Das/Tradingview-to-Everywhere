"""
Quick API Connection Test Script
Tests the Stock Buddy API endpoints
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def main():
    print("=" * 60)
    print("  TTE API Connection Test")
    print("=" * 60)
    print()
    
    # Get API URL from environment
    api_url = os.getenv('STOCK_BUDDY_API_URL', 'https://stock-buddy-app.vercel.app/api/tte')
    print(f"API URL: {api_url}")
    print()
    
    # Test 1: Health Check
    print("[1] Testing Health Check...")
    try:
        # Health endpoint is at /api/health, not /api/tte/health
        health_url = api_url.replace('/tte', '') + '/health'
        print(f"    URL: {health_url}")
        response = requests.get(health_url, timeout=10)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Response: {data}")
            if data.get('status') == 'healthy':
                print("    ✅ Health check PASSED")
            else:
                print("    ⚠️ Health check returned unexpected status")
        else:
            print(f"    ❌ Health check FAILED - HTTP {response.status_code}")
            print(f"    Response: {response.text[:200]}")
    except requests.exceptions.ConnectionError as e:
        print(f"    ❌ Connection Error: {e}")
    except requests.exceptions.Timeout:
        print("    ❌ Request timed out")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    print()
    
    # Test 2: Stats Endpoint
    print("[2] Testing Stats Endpoint...")
    try:
        stats_url = f"{api_url}/stats"
        print(f"    URL: {stats_url}")
        response = requests.get(stats_url, timeout=10)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Success: {data.get('success')}")
            if data.get('data'):
                stats = data['data']
                print(f"    Stats Keys: {list(stats.keys())}")
            print("    ✅ Stats endpoint PASSED")
        else:
            print(f"    ❌ Stats endpoint FAILED - HTTP {response.status_code}")
            print(f"    Response: {response.text[:200]}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    print()
    
    # Test 3: Next Batch Endpoint
    print("[3] Testing Next Batch Endpoint...")
    try:
        batch_url = f"{api_url}/symbols/next-batch?size=5"
        print(f"    URL: {batch_url}")
        response = requests.get(batch_url, timeout=10)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Success: {data.get('success')}")
            if data.get('data'):
                batch = data['data'].get('batch', [])
                print(f"    Batch Count: {len(batch)}")
                if batch:
                    symbols = [s.get('symbol', 'N/A') for s in batch[:3]]
                    print(f"    First 3 Symbols: {symbols}")
            print("    ✅ Next batch endpoint PASSED")
        elif response.status_code == 500:
            data = response.json()
            if 'NOT_INITIALIZED' in str(data):
                print("    ⚠️ Rotation state not initialized (needs seeding)")
            else:
                print(f"    ❌ Server error: {data}")
        else:
            print(f"    ❌ Next batch endpoint FAILED - HTTP {response.status_code}")
            print(f"    Response: {response.text[:200]}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    print()
    
    # Test 4: Hot Symbols Endpoint
    print("[4] Testing Hot Symbols Endpoint...")
    try:
        hot_url = f"{api_url}/hot-symbols?limit=5"
        print(f"    URL: {hot_url}")
        response = requests.get(hot_url, timeout=10)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Success: {data.get('success')}")
            symbols = data.get('data', {}).get('symbols', [])
            print(f"    Hot Symbols Count: {len(symbols)}")
            print("    ✅ Hot symbols endpoint PASSED")
        else:
            print(f"    ❌ Hot symbols endpoint FAILED - HTTP {response.status_code}")
            print(f"    Response: {response.text[:200]}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    print()
    
    # Test 5: Signals Endpoint
    print("[5] Testing Signals Endpoint...")
    try:
        signals_url = f"{api_url}/signals?limit=5"
        print(f"    URL: {signals_url}")
        response = requests.get(signals_url, timeout=10)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    Success: {data.get('success')}")
            signals = data.get('data', {}).get('signals', [])
            print(f"    Signals Count: {len(signals)}")
            print("    ✅ Signals endpoint PASSED")
        else:
            print(f"    ❌ Signals endpoint FAILED - HTTP {response.status_code}")
            print(f"    Response: {response.text[:200]}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("  Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
