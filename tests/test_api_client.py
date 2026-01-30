"""
Tests for the Stock Buddy API Client.

Run with: pytest tests/test_api_client.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from api_client import StockBuddyAPIClient, APIError
from utils.retry import RateLimitError


class TestStockBuddyAPIClient:
    """Test suite for StockBuddyAPIClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = StockBuddyAPIClient(base_url="http://test-api")

    def teardown_method(self):
        """Clean up after tests."""
        self.client.close()

    # ===========================================
    # Health Check Tests
    # ===========================================

    def test_health_check_success(self):
        """Test successful health check."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'success': True, 'status': 'healthy'}
            mock_get.return_value = mock_response

            result = self.client.health_check()

            assert result is True
            mock_get.assert_called_once()

    def test_health_check_failure(self):
        """Test health check when API returns unhealthy."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'success': True, 'status': 'unhealthy'}
            mock_get.return_value = mock_response

            result = self.client.health_check()

            assert result is False

    def test_health_check_connection_error(self):
        """Test health check when connection fails."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection refused")

            result = self.client.health_check()

            assert result is False

    # ===========================================
    # Symbol Batch Tests
    # ===========================================

    def test_get_next_symbol_batch_success(self):
        """Test successful batch retrieval."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'data': [
                    {'symbol': 'EURUSD', 'priority': 'A'},
                    {'symbol': 'GBPUSD', 'priority': 'A'}
                ],
                'batch_number': 1,
                'rotation_number': 0,
                'rotation_progress': '20/1000',
                'count': 2
            }
            mock_get.return_value = mock_response

            result = self.client.get_next_symbol_batch(size=20)

            assert result['success'] is True
            assert len(result['data']) == 2
            assert result['batch_number'] == 1

    def test_get_next_symbol_batch_limits_size(self):
        """Test that batch size is capped at 20."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'success': True, 'data': []}
            mock_get.return_value = mock_response

            self.client.get_next_symbol_batch(size=100)

            # Verify size parameter is capped
            call_args = mock_get.call_args
            assert call_args[1]['params']['size'] == 20

    def test_mark_symbols_scanned(self):
        """Test marking symbols as scanned."""
        with patch.object(self.client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'marked': 5,
                'batch_number': 2,
                'rotation_number': 0
            }
            mock_post.return_value = mock_response

            symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
            result = self.client.mark_symbols_scanned(symbols)

            assert result['success'] is True
            assert result['marked'] == 5

    # ===========================================
    # Hot List Tests
    # ===========================================

    def test_get_hot_symbols(self):
        """Test retrieving hot symbols."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'data': [
                    {'symbol': 'GBPAUD', 'direction': 'bullish', 'nwe_timeframes': ['H4']},
                    {'symbol': 'EURUSD', 'direction': 'bearish', 'nwe_timeframes': ['D1']}
                ],
                'count': 2
            }
            mock_get.return_value = mock_response

            result = self.client.get_hot_symbols(limit=8)

            assert len(result) == 2
            assert result[0]['symbol'] == 'GBPAUD'

    # ===========================================
    # Signal Tests
    # ===========================================

    def test_get_pending_screenshots(self):
        """Test retrieving signals pending screenshots."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'data': [
                    {'id': '123', 'symbol': 'EURUSD', 'status': 'pending_screenshot'}
                ],
                'pagination': {'total': 1}
            }
            mock_get.return_value = mock_response

            result = self.client.get_pending_screenshots(limit=10)

            assert len(result) == 1
            assert result[0]['status'] == 'pending_screenshot'

    def test_update_signal_screenshot(self):
        """Test updating signal with screenshot URL."""
        with patch.object(self.client.session, 'patch') as mock_patch:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'updated': True,
                'signal_id': '123'
            }
            mock_patch.return_value = mock_response

            result = self.client.update_signal_screenshot(
                '123',
                'https://www.tradingview.com/x/ABC123/'
            )

            assert result['success'] is True
            assert result['updated'] is True

    # ===========================================
    # Error Handling Tests
    # ===========================================

    def test_rate_limit_error(self):
        """Test handling of 429 rate limit response."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {'Retry-After': '60'}
            mock_get.return_value = mock_response

            with pytest.raises(RateLimitError) as exc_info:
                # Need to call _handle_response directly since retry decorator would handle it
                self.client._handle_response(mock_response)

            assert exc_info.value.retry_after == 60

    def test_api_error_response(self):
        """Test handling of API error response."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                'success': False,
                'error': 'Invalid request'
            }
            mock_get.return_value = mock_response

            with pytest.raises(APIError) as exc_info:
                self.client._handle_response(mock_response)

            assert 'Invalid request' in str(exc_info.value)
            assert exc_info.value.status_code == 400


class TestAPIClientIntegration:
    """Integration tests that require a running API."""

    @pytest.mark.skip(reason="Requires running API")
    def test_full_workflow(self):
        """Test full API workflow."""
        client = StockBuddyAPIClient()

        try:
            # Health check
            assert client.health_check() is True

            # Get stats
            stats = client.get_stats()
            assert 'signals' in stats

            # Get batch
            batch = client.get_next_symbol_batch()
            assert 'data' in batch

        finally:
            client.close()
