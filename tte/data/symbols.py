"""
Functions for loading symbols from MongoDB.

Currencies - 30
US Stocks - 719
Indian Stocks - 268
Crypto - 19
Indices - 18
"""

from tte import log
import os
from pymongo import MongoClient

# Set up logger for this file
symbol_logger = log.setup_logger(__name__, log.DEBUG)

# MongoDB connection cache
_mongodb_client = None
_mongodb_db = None


def _get_mongodb_connection():
    """Get MongoDB connection with caching. Raises exception if connection fails."""
    global _mongodb_client, _mongodb_db

    if _mongodb_client is None:
        # Get MongoDB connection details from environment variables
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            # Fall back to password-based connection
            pwd = os.getenv("MONGODB_PWD")
            if pwd:
                mongo_uri = f"mongodb+srv://sammy:{pwd}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority"
            else:
                # Use local connection as fallback
                mongo_uri = "mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000"
                symbol_logger.warning(
                    "No MongoDB credentials found in environment, using local connection"
                )

        _mongodb_client = MongoClient(mongo_uri)

        # Test connection - this will raise an exception if it fails
        _mongodb_client.admin.command("ping")

        # Get database
        db_name = os.getenv("MONGODB_DATABASE", "tte")
        _mongodb_db = _mongodb_client[db_name]

        symbol_logger.info("Successfully connected to MongoDB for symbols")

    return _mongodb_db


def _load_symbols_from_mongodb():
    """Load symbols from MongoDB and return in the same format as main_symbols. Raises exception if it fails."""
    db = _get_mongodb_connection()

    symbols_collection = db.symbols

    # Check if collection exists and has data
    doc_count = symbols_collection.count_documents({})
    if doc_count == 0:
        raise ValueError("Symbols collection is empty or does not exist")

    # Group symbols by category
    mongodb_symbols = {}
    for doc in symbols_collection.find({}):
        category = doc.get("category")
        full_symbol = doc.get("full_symbol", doc.get("symbol"))

        if not category or not full_symbol:
            raise ValueError(f"Invalid document in symbols collection: {doc}")

        if category not in mongodb_symbols:
            mongodb_symbols[category] = []

        mongodb_symbols[category].append(full_symbol)

    symbol_logger.info(
        f"Successfully loaded {sum(len(symbols) for symbols in mongodb_symbols.values())} symbols from MongoDB"
    )
    return mongodb_symbols


def _load_symbol_categories_from_mongodb():
    """Load symbol categories from MongoDB and return in the same format as symbol_categories. Raises exception if it fails."""
    db = _get_mongodb_connection()

    symbols_collection = db.symbols

    # Check if collection exists and has data
    doc_count = symbols_collection.count_documents({})
    if doc_count == 0:
        raise ValueError("Symbols collection is empty or does not exist")

    # Create symbol to category mapping
    mongodb_categories = {}
    for doc in symbols_collection.find({}):
        symbol = doc.get("symbol")
        category = doc.get("category")

        if not symbol or not category:
            raise ValueError(f"Invalid document in symbols collection: {doc}")

        mongodb_categories[symbol] = category

    symbol_logger.info(
        f"Successfully loaded {len(mongodb_categories)} symbol categories from MongoDB"
    )
    return mongodb_categories


def get_symbols():
    """Get symbols from MongoDB. Raises exception if MongoDB is unavailable."""
    return _load_symbols_from_mongodb()


def get_symbol_categories():
    """Get symbol categories from MongoDB. Raises exception if MongoDB is unavailable."""
    return _load_symbol_categories_from_mongodb()
