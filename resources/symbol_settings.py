"""
This holds all the functions and variables related to the symbols.

Currencies - 30
US Stocks - 719
Indian Stocks - 268
Crypto - 19
Indices - 18
"""

import logger_setup
from env import *
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Set up logger for this file
symbol_logger = logger_setup.setup_logger(__name__, logger_setup.DEBUG)

# MongoDB connection cache
_mongodb_client = None
_mongodb_db = None


# Initialize empty dictionaries that will be populated from MongoDB
main_symbols = {}
symbol_categories = {}

# this is the same as main_symbols except that each list will have sublists of a certain amount of symbols. The remaining symbols will be in the last sublist
symbol_set = {
    CURRENCIES_WEBHOOK_NAME: [],
    CRYPTO_WEBHOOK_NAME: [],
    INDIAN_STOCKS_WEBHOOK_NAME: [],
    US_STOCKS_WEBHOOK_NAME: [],
}


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


# Update the global symbols and categories to use MongoDB by default
# Skip if SKIP_MONGODB_SYMBOLS is set (used by tiered orchestrator which gets symbols from API)
_skip_mongodb = os.getenv("SKIP_MONGODB_SYMBOLS", "").lower() in ("true", "1", "yes")

if _skip_mongodb:
    symbol_logger.info("SKIP_MONGODB_SYMBOLS is set - skipping MongoDB symbol loading")
else:
    try:
        _mongodb_main_symbols = get_symbols()
        _mongodb_symbol_categories = get_symbol_categories()

        # Update global variables with MongoDB data
        main_symbols.clear()
        main_symbols.update(_mongodb_main_symbols)
        symbol_logger.info("Updated main_symbols with data from MongoDB")

        symbol_categories.clear()
        symbol_categories.update(_mongodb_symbol_categories)
        symbol_logger.info("Updated symbol_categories with data from MongoDB")

    except Exception as e:
        symbol_logger.error(f"Failed to load symbols from MongoDB: {e}")
        symbol_logger.error(
            "Application will not function without MongoDB symbols data"
        )
        raise RuntimeError(f"Critical error: Cannot load symbols from MongoDB: {e}")


def fill_symbol_set(symbol_inputs: int):
    """This fills up the `symbol_set` dictionary. Every key's value is a list with sublists inside it. Each sublist has a maximum of `symbol_inputs` elements. The elements of those sublists are symbols."""
    # Use the MongoDB symbols (will raise exception if MongoDB fails)
    symbols_data = get_symbols()

    for category, symbols in symbols_data.items():
        sublists = [
            symbols[i : i + symbol_inputs]
            for i in range(0, len(symbols), symbol_inputs)
        ]  # Split symbols into sublists of symbol_inputs
        if (
            sublists and len(sublists[-1]) < symbol_inputs
        ):  # If some symbols are remaining
            last_sublist = (
                sublists.pop() if sublists else []
            )  # Pop the last sublist if it exists
            sublists.append(last_sublist)  # Add the remaining symbols in a new sublist
        symbol_set[category] = sublists  # Fill up the symbol_set dictionary

    symbol_logger.info("Filled up symbol_set!")
    return True  # Return True if symbol_set is successfully filled up


def symbol_category(symbol):
    """
    This function returns the symbol category. It retrieves the category of `symbol` (the category can be a US stock, forex pair, crypto pair, etc.)
    """
    # Use the MongoDB categories (will raise exception if MongoDB fails)
    categories = get_symbol_categories()
    return categories.get(symbol, None)
