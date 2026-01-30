"""
Debug script to test the API endpoints directly
"""
import requests
import json

API_BASE = "https://stock-buddy-app.vercel.app/api/tte"

print("=" * 60)
print("  TTE API Debug Test")
print("=" * 60)
print()

# Test 1: Health check
print("[1] Health Check")
try:
    resp = requests.get(f"{API_BASE.replace('/tte', '')}/health", timeout=10)
    print(f"    Status: {resp.status_code}")
    print(f"    Response: {resp.json()}")
except Exception as e:
    print(f"    Error: {e}")
print()

# Test 2: Stats
print("[2] Stats Endpoint")
try:
    resp = requests.get(f"{API_BASE}/stats", timeout=10)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Success: {data.get('success')}")
    if data.get('data'):
        stats = data['data']
        print(f"    Symbols: {stats.get('symbols', {})}")
        print(f"    Rotation: {stats.get('rotation', {})}")
except Exception as e:
    print(f"    Error: {e}")
print()

# Test 3: Next Batch
print("[3] Next Batch Endpoint")
try:
    resp = requests.get(f"{API_BASE}/symbols/next-batch?size=5", timeout=10)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Full Response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"    Error: {e}")
print()

# Test 4: Init status
print("[4] Init Status")
try:
    resp = requests.get(f"{API_BASE}/init", timeout=10)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Full Response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"    Error: {e}")
print()

print("=" * 60)
print("  Debug Complete")
print("=" * 60)
