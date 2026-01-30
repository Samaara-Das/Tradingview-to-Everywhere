"""
Stock Buddy API Client.

Handles all HTTP communication with the Stock Buddy API backend.
Provides methods for symbol rotation, hot list management, and signal updates.
"""

import requests
from typing import List, Dict, Optional, Any
from config import Config
from utils.logger import get_logger
from utils.retry import retry_with_backoff, RateLimitError

logger = get_logger('api_client')


class APIError(Exception):
    """Raised when API returns an error response."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class StockBuddyAPIClient:
    """
    Client for Stock Buddy API interactions.

    Handles all communication with the Stock Buddy backend including:
    - Symbol batch rotation
    - Hot list management
    - Signal CRUD operations
    - System statistics

    Attributes:
        base_url: Base URL for the API (e.g., http://localhost:3000/api)
        session: Requests session for connection pooling
    """

    def __init__(self, base_url: str = None, timeout: int = 30):
        """
        Initialize the API client.

        Args:
            base_url: API base URL (default: from Config.STOCK_BUDDY_API_URL)
            timeout: Default request timeout in seconds
        """
        self.base_url = (base_url or Config.STOCK_BUDDY_API_URL).rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TTE-Orchestrator/1.0'
        })

        logger.info(f"API client initialized: {self.base_url}")

    def _handle_response(self, response: requests.Response) -> dict:
        """
        Handle API response and errors.

        Args:
            response: Response object from requests

        Returns:
            Parsed JSON response data

        Raises:
            RateLimitError: If API returns 429
            APIError: If API returns error status
        """
        # Check for rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            raise RateLimitError(retry_after)

        # Try to parse JSON
        try:
            data = response.json()
        except ValueError:
            data = {'error': response.text}

        # Check for HTTP errors
        if response.status_code >= 400:
            error_msg = data.get('error', f'HTTP {response.status_code}')
            raise APIError(error_msg, response.status_code, data)

        # Check for API-level errors
        if not data.get('success', True):
            raise APIError(data.get('error', 'Unknown API error'), response.status_code, data)

        return data

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def _post(self, endpoint: str, data: dict = None) -> dict:
        """Make POST request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data, timeout=self.timeout)
        return self._handle_response(response)

    def _patch(self, endpoint: str, data: dict = None) -> dict:
        """Make PATCH request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.patch(url, json=data, timeout=self.timeout)
        return self._handle_response(response)

    # ===========================================
    # Health & Stats
    # ===========================================

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def health_check(self) -> bool:
        """
        Check API health status.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Health endpoint is at /api/health, not /api/tte/health
            # So we need to go up one level from base_url
            health_url = self.base_url.replace('/tte', '') + '/health'
            response = self.session.get(health_url, timeout=self.timeout)
            data = response.json()
            return data.get('status') == 'healthy'
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.

        Returns:
            Statistics data including signals, hot_list, and rotation info
        """
        data = self._get('/stats')
        return data.get('data', {})

    # ===========================================
    # Symbol Rotation
    # ===========================================

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def get_next_symbol_batch(self, size: int = 20) -> Dict[str, Any]:
        """
        Get next batch of symbols for NWE screener rotation.

        Args:
            size: Number of symbols to fetch (max 20)

        Returns:
            Dict containing:
                - batch: List of symbol objects
                - count: Number of symbols in batch
                - rotation: Rotation state info
        """
        data = self._get('/symbols/next-batch', params={'size': min(size, 20)})

        # API returns batch at root level, not nested under 'data'
        batch = data.get('batch', [])
        rotation = data.get('rotation', {})
        
        logger.debug(
            f"Got batch #{rotation.get('batch_number', '?')}: "
            f"{len(batch)} symbols"
        )

        return {
            'success': data.get('success', True),
            'batch': batch,
            'count': data.get('count', len(batch)),
            'rotation': rotation
        }

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def mark_symbols_scanned(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Mark symbols as scanned after NWE screener processes them.

        Args:
            symbols: List of symbol names that were scanned

        Returns:
            Dict with marked count and batch state
        """
        data = self._post('/symbols/mark-scanned', {'symbols': symbols})

        logger.info(
            f"Marked {data.get('marked', 0)} symbols scanned. "
            f"Batch #{data.get('batch_number', '?')}"
        )

        return data

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_symbols(
        self,
        limit: int = 100,
        offset: int = 0,
        priority: str = None,
        active: bool = None
    ) -> Dict[str, Any]:
        """
        Get symbols with optional filtering.

        Args:
            limit: Max symbols to return
            offset: Pagination offset
            priority: Filter by priority (A, B, C)
            active: Filter by active status

        Returns:
            Dict with data array and pagination info
        """
        params = {'limit': limit, 'offset': offset}
        if priority:
            params['priority'] = priority
        if active is not None:
            params['active'] = active

        return self._get('/symbols', params=params)

    # ===========================================
    # Hot List (Tier 2 Queue)
    # ===========================================

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def get_hot_symbols(self, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Get symbols pending Tier 2 (OBDIV) processing.

        Args:
            limit: Maximum number of symbols to return (max 20)

        Returns:
            List of hot symbol objects with direction and timeframes
        """
        data = self._get('/hot-symbols', params={
            'limit': min(limit, 20),
            'status': 'pending_tier2'
        })

        # API may return symbols at root level or under 'data'
        hot_symbols = data.get('symbols', data.get('data', {}).get('symbols', []))
        if hot_symbols:
            symbols_list = [s['symbol'] for s in hot_symbols]
            logger.debug(f"Hot symbols: {symbols_list}")

        return hot_symbols

    # ===========================================
    # Signals
    # ===========================================

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def get_pending_screenshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get signals pending screenshot capture.

        Args:
            limit: Maximum number of signals to return

        Returns:
            List of signal objects needing screenshots
        """
        data = self._get('/signals', params={
            'status': 'pending_screenshot',
            'limit': limit
        })

        # API may return signals at root level or under 'data'
        return data.get('signals', data.get('data', {}).get('signals', []))

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def get_signals(
        self,
        limit: int = 50,
        offset: int = 0,
        level: int = None,
        direction: str = None,
        symbol: str = None,
        status: str = None
    ) -> Dict[str, Any]:
        """
        Get signals with optional filtering.

        Args:
            limit: Max signals to return
            offset: Pagination offset
            level: Filter by signal level (1, 2, 3)
            direction: Filter by direction (bullish, bearish)
            symbol: Filter by symbol
            status: Filter by status (pending_screenshot, complete)

        Returns:
            Dict with data array and pagination info
        """
        params = {'limit': limit, 'offset': offset}
        if level:
            params['level'] = level
        if direction:
            params['direction'] = direction
        if symbol:
            params['symbol'] = symbol
        if status:
            params['status'] = status

        return self._get('/signals', params=params)

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def update_signal_screenshot(
        self,
        signal_id: str,
        screenshot_url: str,
        status: str = 'complete'
    ) -> Dict[str, Any]:
        """
        Update signal with screenshot URL.

        Args:
            signal_id: Signal ID to update
            screenshot_url: URL of captured screenshot
            status: New status (default: 'complete')

        Returns:
            Update result
        """
        data = self._patch(f'/signals/{signal_id}', {
            'screenshot_url': screenshot_url,
            'status': status
        })

        logger.info(f"Updated signal {signal_id} with screenshot")

        return data

    # ===========================================
    # Cleanup
    # ===========================================

    def close(self):
        """Close the session."""
        self.session.close()
        logger.debug("API client session closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
