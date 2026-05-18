"""
Functions for loading symbols from MongoDB.

Counts below were taken from a live `db.symbols` aggregation on 2026-05-15
(~677 symbols total). Treat them as a snapshot — the collection is mutated
by upstream seeders and the live count drifts.

  Indian Stocks - 387
  US Stocks     - 243
  Currencies    - 29
  Crypto        - 18
"""

import os

from pymongo import MongoClient

from tte import log
from tte.config import INSTANCE

# Set up logger for this file
symbol_logger = log.setup_logger(__name__, log.DEBUG)

# MongoDB connection cache
_mongodb_client = None
_mongodb_db = None


def _get_mongodb_connection():
    """Get MongoDB connection with caching. Raises exception if connection fails."""
    global _mongodb_client, _mongodb_db

    if _mongodb_client is None:
        # Get MongoDB connection string from environment
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            raise ValueError(
                "MONGODB_URI environment variable is required. "
                "Set it in .env (e.g. mongodb+srv://user:pass@host/...)"
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
    """Load symbols from MongoDB and return in the same format as main_symbols.

    WS-A multi-instance: returns ONLY rows tagged with this container's
    `assigned_instance` (matches `INSTANCE` env). Docs that pre-date the
    assigned_instance field default to `tte-1` so legacy single-instance
    deployments continue to see all rows. Raises if the collection is
    empty or a doc is malformed.
    """
    db = _get_mongodb_connection()

    symbols_collection = db.symbols

    # Check if collection exists and has data
    doc_count = symbols_collection.count_documents({})
    if doc_count == 0:
        raise ValueError("Symbols collection is empty or does not exist")

    # Match this instance's slice (and legacy untagged docs for tte-1)
    if INSTANCE == "tte-1":
        query: dict = {
            "$or": [{"assigned_instance": "tte-1"}, {"assigned_instance": {"$exists": False}}]
        }
    else:
        query = {"assigned_instance": INSTANCE}

    # Group symbols by category
    mongodb_symbols: dict = {}
    for doc in symbols_collection.find(query):
        category = doc.get("category")
        full_symbol = doc.get("full_symbol", doc.get("symbol"))

        if not category or not full_symbol:
            raise ValueError(f"Invalid document in symbols collection: {doc}")

        if category not in mongodb_symbols:
            mongodb_symbols[category] = []

        mongodb_symbols[category].append(full_symbol)

    symbol_logger.info(
        f"Loaded {sum(len(symbols) for symbols in mongodb_symbols.values())} symbols "
        f"for INSTANCE={INSTANCE} from MongoDB"
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
