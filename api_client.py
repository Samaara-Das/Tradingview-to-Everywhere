"""
Stock Buddy API Client for TTE Tiered Orchestrator.

Handles communication with the Stock Buddy API for:
- Fetching symbol batches for NWE scanning
- Marking symbols as scanned
- Fetching hot symbols for OBDIV processing
"""

import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class StockBuddyAPIClient:
    """Client for interacting with the Stock Buddy TTE API."""

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API (e.g., https://stock-buddy-app.vercel.app/api/tte)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def health_check(self) -> bool:
        """
        Check if the API is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Health endpoint is at /api/health, not /api/tte/health
            health_url = self.base_url.replace("/api/tte", "/api/health")
            response = self.session.get(health_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_stats(self) -> Optional[Dict]:
        """
        Get system statistics.

        Returns:
            Stats dictionary or None on error
        """
        try:
            response = self.session.get(f"{self.base_url}/stats", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return None

    def get_next_symbol_batch(self, size: int = 20) -> Dict:
        """
        Get the next batch of symbols for NWE scanning.

        Args:
            size: Number of symbols to fetch (default 20, max for NWE screener)

        Returns:
            Dictionary with batch info:
            {
                "success": true,
                "batch": [{"symbol": "OANDA:EURUSD", ...}, ...],
                "count": 20,
                "batch_number": 6,
                "rotation_number": 1,
                "total_symbols": 941,
                "symbols_scanned_this_rotation": 120
            }
        """
        try:
            response = self.session.get(
                f"{self.base_url}/symbols/next-batch",
                params={"size": size},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            # Extract rotation info from nested structure
            rotation = data.get("rotation", {})
            batch_number = rotation.get("batch_number", "?")
            rotation_number = rotation.get("rotation_number", "?")
            total_symbols = rotation.get("total_symbols", "?")
            scanned = rotation.get("symbols_scanned_this_rotation", 0)

            # Flatten rotation info to top level for easier access
            data["batch_number"] = batch_number
            data["rotation_number"] = rotation_number
            data["total_symbols"] = total_symbols
            data["symbols_scanned_this_rotation"] = scanned

            logger.info(
                f"Fetched batch #{batch_number} with {len(data.get('batch', []))} symbols "
                f"(rotation {rotation_number}, {scanned}/{total_symbols} scanned)"
            )
            return data
        except Exception as e:
            logger.error(f"Failed to get next symbol batch: {e}")
            return {"success": False, "batch": [], "error": str(e)}

    def mark_symbols_scanned(self, symbols: List[str]) -> Dict:
        """
        Mark symbols as scanned after NWE processing.

        Args:
            symbols: List of symbol strings that were scanned

        Returns:
            Response dictionary
        """
        try:
            response = self.session.post(
                f"{self.base_url}/symbols/mark-scanned",
                json={"symbols": symbols},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Marked {len(symbols)} symbols as scanned")
            return data
        except Exception as e:
            logger.error(f"Failed to mark symbols as scanned: {e}")
            return {"success": False, "error": str(e)}

    def get_hot_symbols(self, limit: int = 10) -> List[Dict]:
        """
        Get hot symbols that need OBDIV processing.

        Args:
            limit: Maximum number of symbols to fetch

        Returns:
            List of hot symbol dictionaries:
            [
                {
                    "symbol": "GBPAUD",
                    "direction": "bullish",
                    "nwe_timeframe": "5m",
                    "status": "pending_tier2"
                },
                ...
            ]
        """
        try:
            url = f"{self.base_url}/hot-symbols"
            params = {"limit": limit, "status": "pending_tier2"}
            print(f"[DEBUG] GET {url} with params: {params}", flush=True)

            response = self.session.get(url, params=params, timeout=self.timeout)
            print(f"[DEBUG] Response status: {response.status_code}", flush=True)
            print(f"[DEBUG] Response body: {response.text[:500]}", flush=True)

            response.raise_for_status()
            data = response.json()
            # API returns {"success": true, "symbols": [...]} not {"data": [...]}
            hot_symbols = data.get("symbols", [])
            logger.info(f"Fetched {len(hot_symbols)} hot symbols pending Tier 2")
            return hot_symbols
        except Exception as e:
            print(f"[DEBUG] get_hot_symbols error: {e}", flush=True)
            logger.error(f"Failed to get hot symbols: {e}")
            return []

    def get_all_symbols(self) -> List[str]:
        """Get all symbols from Stock Buddy API. Returns flat list.

        This is a future fallback for combo mode — the endpoint doesn't exist yet.
        Primary symbol source is MongoDB via symbol_settings.get_symbols().
        """
        try:
            response = self.session.get(
                f"{self.base_url}/symbols", timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            symbols = [
                s.get("symbol", s) if isinstance(s, dict) else s
                for s in data.get("symbols", [])
            ]
            logger.info(f"Fetched {len(symbols)} symbols from API")
            return symbols
        except Exception as e:
            logger.error(f"Failed to get all symbols: {e}")
            return []

    def delete_expired_hot_symbols(self) -> Dict:
        """
        Delete all expired hot symbols from the database.
        Called at startup to clean up stale entries.

        Returns:
            Response dictionary with deleted_count and success status
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/hot-symbols/expired",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            deleted_count = data.get("deleted_count", 0)
            logger.info(f"Deleted {deleted_count} expired hot symbols")
            return {"success": True, "deleted_count": deleted_count}
        except Exception as e:
            logger.error(f"Failed to delete expired hot symbols: {e}")
            return {"success": False, "error": str(e)}

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
