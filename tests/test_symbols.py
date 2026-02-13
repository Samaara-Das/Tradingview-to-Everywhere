"""Tests for tte/data/symbols.py — MongoDB symbol loading."""

from unittest.mock import Mock, patch, MagicMock
import pytest

from tte.data.symbols import (
    get_symbols,
    get_symbol_categories,
    _load_symbols_from_mongodb,
    _load_symbol_categories_from_mongodb,
)


class TestLoadSymbolsFromMongoDB:
    """Test _load_symbols_from_mongodb() function."""

    @patch("tte.data.symbols._get_mongodb_connection")
    def test_load_symbols_groups_by_category(self, mock_get_connection):
        """Symbols should be grouped by category correctly."""
        # Mock database and collection
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.symbols = mock_collection
        mock_get_connection.return_value = mock_db

        # Mock data
        mock_collection.count_documents.return_value = 3
        mock_collection.find.return_value = [
            {"category": "US Stocks", "full_symbol": "NASDAQ:AAPL"},
            {"category": "US Stocks", "full_symbol": "NYSE:MSFT"},
            {"category": "Crypto", "full_symbol": "BINANCE:BTCUSDT"},
        ]

        result = _load_symbols_from_mongodb()

        assert "US Stocks" in result
        assert "Crypto" in result
        assert result["US Stocks"] == ["NASDAQ:AAPL", "NYSE:MSFT"]
        assert result["Crypto"] == ["BINANCE:BTCUSDT"]

    @patch("tte.data.symbols._get_mongodb_connection")
    def test_load_symbols_uses_symbol_fallback(self, mock_get_connection):
        """Should use 'symbol' field when 'full_symbol' is missing."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.symbols = mock_collection
        mock_get_connection.return_value = mock_db

        mock_collection.count_documents.return_value = 1
        mock_collection.find.return_value = [
            {"category": "Indices", "symbol": "SPX"},
        ]

        result = _load_symbols_from_mongodb()

        assert result["Indices"] == ["SPX"]

    @patch("tte.data.symbols._get_mongodb_connection")
    def test_load_symbols_raises_on_empty_collection(self, mock_get_connection):
        """Empty collection should raise ValueError."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.symbols = mock_collection
        mock_get_connection.return_value = mock_db

        mock_collection.count_documents.return_value = 0

        with pytest.raises(ValueError, match="Symbols collection is empty"):
            _load_symbols_from_mongodb()

    @patch("tte.data.symbols._get_mongodb_connection")
    def test_load_symbols_raises_on_invalid_document(self, mock_get_connection):
        """Invalid document (missing category or symbol) should raise ValueError."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.symbols = mock_collection
        mock_get_connection.return_value = mock_db

        mock_collection.count_documents.return_value = 1
        mock_collection.find.return_value = [
            {"category": "US Stocks"},  # Missing symbol
        ]

        with pytest.raises(ValueError, match="Invalid document"):
            _load_symbols_from_mongodb()


class TestLoadSymbolCategoriesFromMongoDB:
    """Test _load_symbol_categories_from_mongodb() function."""

    @patch("tte.data.symbols._get_mongodb_connection")
    def test_load_categories_creates_symbol_to_category_mapping(
        self, mock_get_connection
    ):
        """Should create correct symbol→category mapping."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.symbols = mock_collection
        mock_get_connection.return_value = mock_db

        mock_collection.count_documents.return_value = 3
        mock_collection.find.return_value = [
            {"symbol": "AAPL", "category": "US Stocks"},
            {"symbol": "BTCUSDT", "category": "Crypto"},
            {"symbol": "SPX", "category": "Indices"},
        ]

        result = _load_symbol_categories_from_mongodb()

        assert result["AAPL"] == "US Stocks"
        assert result["BTCUSDT"] == "Crypto"
        assert result["SPX"] == "Indices"

    @patch("tte.data.symbols._get_mongodb_connection")
    def test_load_categories_raises_on_empty_collection(self, mock_get_connection):
        """Empty collection should raise ValueError."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.symbols = mock_collection
        mock_get_connection.return_value = mock_db

        mock_collection.count_documents.return_value = 0

        with pytest.raises(ValueError, match="Symbols collection is empty"):
            _load_symbol_categories_from_mongodb()

    @patch("tte.data.symbols._get_mongodb_connection")
    def test_load_categories_raises_on_invalid_document(self, mock_get_connection):
        """Invalid document (missing symbol or category) should raise ValueError."""
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.symbols = mock_collection
        mock_get_connection.return_value = mock_db

        mock_collection.count_documents.return_value = 1
        mock_collection.find.return_value = [
            {"symbol": "AAPL"},  # Missing category
        ]

        with pytest.raises(ValueError, match="Invalid document"):
            _load_symbol_categories_from_mongodb()


class TestPublicFunctions:
    """Test public get_symbols() and get_symbol_categories() functions."""

    @patch("tte.data.symbols._load_symbols_from_mongodb")
    def test_get_symbols_calls_internal_loader(self, mock_load_symbols):
        """get_symbols() should call _load_symbols_from_mongodb()."""
        mock_load_symbols.return_value = {"US Stocks": ["AAPL", "MSFT"]}
        result = get_symbols()
        assert result == {"US Stocks": ["AAPL", "MSFT"]}
        mock_load_symbols.assert_called_once()

    @patch("tte.data.symbols._load_symbol_categories_from_mongodb")
    def test_get_symbol_categories_calls_internal_loader(self, mock_load_categories):
        """get_symbol_categories() should call _load_symbol_categories_from_mongodb()."""
        mock_load_categories.return_value = {"AAPL": "US Stocks"}
        result = get_symbol_categories()
        assert result == {"AAPL": "US Stocks"}
        mock_load_categories.assert_called_once()
