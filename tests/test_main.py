"""Tests for tte/main.py — chunk_symbols() function."""

from tte.main import chunk_symbols


class TestChunkSymbols:
    """Test the chunk_symbols() function for batching symbols."""

    def test_chunk_symbols_with_empty_list(self):
        """Empty list should return empty result."""
        result = chunk_symbols([], size=3)
        assert result == []

    def test_chunk_symbols_with_exact_batch_size(self):
        """Symbols matching exact batch size should return single chunk."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        result = chunk_symbols(symbols, size=3)
        assert result == [["AAPL", "GOOGL", "MSFT"]]

    def test_chunk_symbols_with_remainder(self):
        """Symbols with remainder should create correct last chunk."""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        result = chunk_symbols(symbols, size=3)
        assert result == [["AAPL", "GOOGL", "MSFT"], ["TSLA", "AMZN"]]

    def test_chunk_symbols_with_single_item(self):
        """Single item should return single chunk with one element."""
        symbols = ["AAPL"]
        result = chunk_symbols(symbols, size=3)
        assert result == [["AAPL"]]

    def test_chunk_symbols_with_batch_size_one(self):
        """batch_size=1 should create individual chunks for each symbol."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        result = chunk_symbols(symbols, size=1)
        assert result == [["AAPL"], ["GOOGL"], ["MSFT"]]

    def test_chunk_symbols_with_multiple_full_batches(self):
        """Multiple full batches should all be the same size except possibly the last."""
        symbols = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
        result = chunk_symbols(symbols, size=4)
        assert result == [["A", "B", "C", "D"], ["E", "F", "G", "H"], ["I"]]

    def test_chunk_symbols_preserves_order(self):
        """Original symbol order should be preserved in chunks."""
        symbols = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
        result = chunk_symbols(symbols, size=2)
        assert result == [["FIRST", "SECOND"], ["THIRD", "FOURTH"], ["FIFTH"]]
        # Verify order within each chunk
        assert result[0][0] == "FIRST"
        assert result[0][1] == "SECOND"
        assert result[1][0] == "THIRD"
