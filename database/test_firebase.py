"""
Firebase Connection Test Script

Purpose: This script tests the connection to Firebase Firestore and attempts to add a test document.

Functionality: This script provides a simple way to verify Firebase connectivity:
1. Initializes a Firebase Database connection
2. Adds a test document to the specified collection
3. Verifies the document was added successfully
4. Optionally tests retrieving documents with various query methods

Dependencies:
- database/firebase_db.py: For Firebase Database class
- time: For Unix timestamp generation
- env.py: For environment variables and configuration

Usage: Run this script to test Firebase connectivity and basic operations
"""

import sys
import os
import time
import traceback

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.firebase_db import Database
from env import COLLECTION


def test_firebase_connection():
    """Test connection to Firebase and basic operations"""
    try:
        print("Testing Firebase connection...")

        # Initialize database connection
        print("Initializing Database instance...")
        db = Database("")
        print("Database connection initialized")

        # Create test document
        test_doc = {
            "direction": "test",
            "symbol": "TEST/USD",
            "timeframe": "1h",
            "entryPrice": 100.0,
            "tp1Price": 110.0,
            "tp2Price": 120.0,
            "tp3Price": 130.0,
            "slPrice": 90.0,
            "tvEntrySnapshot": "https://test.com/entry.png",
            "pngEntrySnapshot": "https://test.com/entry.png",
            "content": "Test entry",
            "unixTime": int(time.time() * 1000),  # Current time in milliseconds
            "category": "Test",
            "isSlHit": False,
            "isTp1Hit": False,
            "isTp2Hit": False,
            "isTp3Hit": False,
            "tvExitSnapshot": "",
            "pngExitSnapshot": "",
        }

        # Add document to test collection
        collection_name = "TestEntries"
        print(f"Adding test document to '{collection_name}' collection...")
        success = db.add_doc(test_doc, collection_name)

        if success:
            print(f"Successfully added test document to '{collection_name}' collection")
        else:
            print(f"Failed to add test document to '{collection_name}' collection")
            return False

        # Test getting latest document
        print(f"Retrieving latest document from '{collection_name}' collection...")
        latest_doc = db.get_latest_doc(collection_name)
        if latest_doc:
            print(
                f"Successfully retrieved latest document from '{collection_name}' collection"
            )
            print(f"Document data: {latest_doc}")
        else:
            print(
                f"Failed to retrieve latest document from '{collection_name}' collection"
            )

        # Test get_entries_in_timespan
        start_time = int(time.time()) - 3600  # 1 hour ago
        print(f"Retrieving entries in timespan from '{collection_name}' collection...")
        print(f"Start time: {start_time}")
        entries = db.get_entries_in_timespan(collection_name, "Test", start_time)
        if entries:
            print(f"Successfully retrieved {len(entries)} entries in timespan")
        else:
            print("No entries found in timespan or query failed")

        # Now test the actual Entries collection
        print(f"\nTesting the {COLLECTION} collection...")

        # Add document to Entries collection
        print(f"Adding test document to '{COLLECTION}' collection...")
        test_doc["symbol"] = "TEST/ENTRIES"  # Modify the symbol to distinguish it
        success = db.add_doc(test_doc, COLLECTION)

        if success:
            print(f"Successfully added test document to '{COLLECTION}' collection")
        else:
            print(f"Failed to add test document to '{COLLECTION}' collection")

        # Test getting latest document from Entries
        print(f"Retrieving latest document from '{COLLECTION}' collection...")
        latest_doc = db.get_latest_doc(COLLECTION)
        if latest_doc:
            print(
                f"Successfully retrieved latest document from '{COLLECTION}' collection"
            )
            print(f"Document data: {latest_doc}")
        else:
            print(f"Failed to retrieve latest document from '{COLLECTION}' collection")

        print("Firebase connection test completed")
        return True
    except Exception as e:
        print(f"Exception during test: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_firebase_connection()
