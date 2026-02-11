> **ARCHIVED** — All 89 implementation tasks completed Feb 2026. This document is kept as historical reference. For current combo mode documentation, see [PRD.md](PRD.md).

---

# Combo Screener Implementation Guide

This document provides step-by-step implementation instructions for converting the TTE system from the two-tier architecture (NWE + OBDIV) to the single combo screener architecture. Each section specifies the exact file, exact changes, and exact code to write.

---

## Table of Contents

1. [Task Overview](#1-task-overview)
2. [Task 1: Update Pine Script Timeframe Labels](#2-task-1-update-pine-script-timeframe-labels)
3. [Task 2: Rewrite config.py](#3-task-2-rewrite-configpy)
4. [Task 3: Rewrite api_client.py](#4-task-3-rewrite-api_clientpy)
5. [Task 4: Rewrite orchestrator.py](#5-task-4-rewrite-orchestratorpy)
6. [Task 5: Create combo_main.py](#6-task-5-create-combo_mainpy)
7. [Task 6: Update CLAUDE.md](#7-task-6-update-claudemd)
8. [Dependencies Between Tasks](#8-dependencies-between-tasks)
9. [What NOT to Change](#9-what-not-to-change)

---

## 1. Task Overview

There are **6 implementation tasks**. Tasks 1, 2, and 3 are independent and can be done in parallel. Task 4 depends on Tasks 2 and 3. Task 5 depends on Task 4. Task 6 can be done any time.

| Task | File(s) | Effort | Depends On |
|------|---------|--------|------------|
| 1. Pine Script timeframe labels | `Pine Script Code/TTE Screener.txt` | Small | None |
| 2. Rewrite config.py | `config.py` | Small | None |
| 3. Rewrite api_client.py | `api_client.py` | Small | None |
| 4. Rewrite orchestrator.py | `orchestrator.py` | Large | Tasks 2, 3 |
| 5. Create combo_main.py | `combo_main.py` (new file) | Medium | Task 4 |
| 6. Update CLAUDE.md | `CLAUDE.md` | Small | None |

---

## 2. Task 1: Update Pine Script Timeframe Labels

### File: `Pine Script Code/TTE Screener.txt`

### Problem

The Pine Script variable names (`TF_H4`, `TF_D1`, `TF_W1`) are legacy names that don't match the actual production timeframes. The JSON payload currently outputs `"H4"`, `"D1"`, `"W1"` as timeframe labels, but the actual production timeframes are:

| Variable | Production Value | Actual Timeframe | Current Label | Correct Label |
|----------|-----------------|-------------------|---------------|---------------|
| `TF_H4` | `"60"` | 1 Hour | `"H4"` | `"1H"` |
| `TF_D1` | `"240"` | 4 Hour | `"D1"` | `"H4"` |
| `TF_W1` | `"D"` | Daily | `"W1"` | `"D1"` |

### Changes Required

**DO NOT rename the Pine Script variables** (`TF_H4`, `TF_D1`, `TF_W1`). Only change the **string literals** that appear in the JSON payload and display table.

#### 2.1 Update the indicator description comment (lines 4-12)

Change:
```
// - Nadaraya-Watson Envelope (NWE) on H4 and Daily
// - Order Block & FVG detection on H4, Daily, and Weekly
// - Kernel AO Divergence (Logic 2) on H4 and Daily
```
To:
```
// - Nadaraya-Watson Envelope (NWE) on 1H and H4
// - Order Block & FVG detection on 1H, H4, and D1
// - Kernel AO Divergence (Logic 2) on 1H and H4
// NOTE: Variable names TF_H4/TF_D1/TF_W1 are legacy. Actual timeframes: 1H/H4/D1.
```

#### 2.2 Update `buildNweDetailTable` function (line ~817)

This function builds the display table labels. Change all `'H4'` to `'1H'` and all `'D1'` to `'H4'`:

```pine
buildNweDetailTable(bool h4, bool d1) =>
    string result = ''
    if h4
        result := '1H'       // was 'H4'
        result
    if d1
        result := result + (str.length(result) > 0 ? ',' : '') + 'H4'    // was 'D1'
        result
    result
```

#### 2.3 Update `buildObDetailTable` function (line ~828)

Change `'H4'` to `'1H'`, `'D1'` to `'H4'`, and `'W1'` to `'D1'`:

```pine
buildObDetailTable(int h4, int d1, int w1) =>
    string result = ''
    if h4 == 1
        result := '1H'       // was 'H4'
        result
    if d1 == 1
        result := result + (str.length(result) > 0 ? ',' : '') + 'H4'    // was 'D1'
        result
    if w1 == 1
        result := result + (str.length(result) > 0 ? ',' : '') + 'D1'    // was 'W1'
        result
    result
```

#### 2.4 Update `buildDivDetailTable` function (line ~842)

Same pattern:

```pine
buildDivDetailTable(int divH4, int divD1, int currTime) =>
    string result = ''
    if divH4 == currTime
        result := '1H'       // was 'H4'
        result
    if divD1 == currTime
        result := result + (str.length(result) > 0 ? ',' : '') + 'H4'    // was 'D1'
        result
    result
```

#### 2.5 Update `buildNweArray` function (line ~865)

Change the string literals passed to `buildNweEntry`:

```pine
buildNweArray(...) =>
    string e1 = buildNweEntry(bullH4, bullZoneH4, 'bullish', '1H', overlapTime)    // was 'H4'
    string e2 = buildNweEntry(bearH4, bearZoneH4, 'bearish', '1H', overlapTime)    // was 'H4'
    string e3 = buildNweEntry(bullD1, bullZoneD1, 'bullish', 'H4', overlapTime)    // was 'D1'
    string e4 = buildNweEntry(bearD1, bearZoneD1, 'bearish', 'H4', overlapTime)    // was 'D1'
    joinEntries4(e1, e2, e3, e4)
```

#### 2.6 Update `buildObArray` function (line ~873)

Change the string literals passed to `buildObEntry`:

```pine
buildObArray(...) =>
    string e1 = buildObEntry(bullFH4, bullZTH4, bullTH4, bullTmH4, overlapTime, '1H', true)    // was 'H4'
    string e2 = buildObEntry(bearFH4, bearZTH4, bearTH4, bearTmH4, overlapTime, '1H', false)   // was 'H4'
    string e3 = buildObEntry(bullFD1, bullZTD1, bullTD1, bullTmD1, overlapTime, 'H4', true)     // was 'D1'
    string e4 = buildObEntry(bearFD1, bearZTD1, bearTD1, bearTmD1, overlapTime, 'H4', false)    // was 'D1'
    string e5 = buildObEntry(bullFW1, bullZTW1, bullTW1, bullTmW1, overlapTime, 'D1', true)     // was 'W1'
    string e6 = buildObEntry(bearFW1, bearZTW1, bearTW1, bearTmW1, overlapTime, 'D1', false)    // was 'W1'
    joinEntries6(e1, e2, e3, e4, e5, e6)
```

#### 2.7 Update `buildDivArray` function (line ~883)

Change the string literals passed to `buildDivEntry`:

```pine
buildDivArray(...) =>
    string e1 = buildDivEntry(divBullH4, currTime, '1H', 'bullish')    // was 'H4'
    string e2 = buildDivEntry(divBearH4, currTime, '1H', 'bearish')    // was 'H4'
    string e3 = buildDivEntry(divBullD1, currTime, 'H4', 'bullish')    // was 'D1'
    string e4 = buildDivEntry(divBearD1, currTime, 'H4', 'bearish')    // was 'D1'
    joinEntries4(e1, e2, e3, e4)
```

#### 2.8 Update `request.security` comments (lines ~681, ~688, ~695)

Update the comments above the request.security blocks:
- `// H4 timeframe` → `// 1H timeframe (via TF_H4)`
- `// Daily timeframe` → `// H4 timeframe (via TF_D1)`
- `// Weekly timeframe` → `// D1 timeframe (via TF_W1)`

### Summary of all string literal changes

| Location | Old | New |
|----------|-----|-----|
| TF_H4 data sections | `'H4'` | `'1H'` |
| TF_D1 data sections | `'D1'` | `'H4'` |
| TF_W1 data sections | `'W1'` | `'D1'` |

**Total locations**: ~18 string literal changes across 7 functions/comments.

---

## 3. Task 2: Rewrite config.py

### File: `config.py`

### Current State

The current config has tiered-architecture-specific fields: `nwe_chart_url`, `obdiv_chart_url`, `nwe_batch_size`, `obdiv_batch_size`, `nwe_batch_wait`, `obdiv_batch_wait`.

### New Config

Replace the entire `Config` class with combo screener settings:

```python
"""
Configuration module for the TTE Combo Screener Orchestrator.
Loads settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration settings for the combo screener orchestrator."""

    # Stock Buddy API
    api_base_url: str = os.getenv(
        "STOCK_BUDDY_API_URL", "https://stock-buddy-app.vercel.app/api/tte"
    )
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))

    # Webhook URL for TradingView alerts (Stock Buddy signal endpoint)
    webhook_url: str = os.getenv(
        "WEBHOOK_URL", "https://stock-buddy-app.vercel.app/api/tte/signal"
    )

    # TradingView chart URL (layout with TTE Screener indicator)
    chart_url: str = os.getenv("CHART_URL", "")

    # Layout name in TradingView (must have TTE Screener indicator)
    layout_name: str = os.getenv("LAYOUT_NAME", "Screener")

    # Batch size (hard limit: 4 symbols per screener instance)
    batch_size: int = int(os.getenv("BATCH_SIZE", "4"))

    # Alert creation timing (seconds between creating each alert)
    alert_creation_delay: int = int(os.getenv("ALERT_CREATION_DELAY", "5"))

    # Maintenance settings (seconds between stopped-alert checks)
    maintenance_interval: int = int(os.getenv("MAINTENANCE_INTERVAL", "1800"))

    # Chrome settings
    chrome_profile: str = os.getenv("CHROME_PROFILE", "Profile 2")
    chrome_profiles_path: str = os.getenv("CHROME_PROFILES_PATH", "")
    headless: bool = os.getenv("HEADLESS", "false").lower() == "true"

    # Orchestrator settings
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay: int = int(os.getenv("RETRY_DELAY", "5"))

    # Screener indicator names (as shown in TradingView legend)
    screener_shorttitle: str = "Screener"
    screener_name: str = "TTE Screener"

    def validate(self) -> list[str]:
        """Validate required configuration. Returns list of missing/invalid fields."""
        errors = []

        if not self.api_base_url:
            errors.append("STOCK_BUDDY_API_URL is required")

        if not self.chart_url:
            errors.append("CHART_URL is required (TradingView chart with TTE Screener)")

        if not self.webhook_url:
            errors.append("WEBHOOK_URL is required (Stock Buddy signal endpoint)")

        if self.batch_size < 1 or self.batch_size > 4:
            errors.append("BATCH_SIZE must be between 1 and 4 (TTE Screener hard limit)")

        if self.maintenance_interval < 60:
            errors.append("MAINTENANCE_INTERVAL must be at least 60 seconds")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0


# Global config instance
config = Config()
```

### Key differences from current config

| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `nwe_chart_url` | `chart_url` | Single chart URL instead of two |
| `obdiv_chart_url` | *(removed)* | No OBDIV layout needed |
| `nwe_batch_size` (default 20) | `batch_size` (default 4) | Hard limit of 4 symbols |
| `obdiv_batch_size` (default 8) | *(removed)* | No OBDIV phase |
| `nwe_batch_wait` | *(removed)* | No waiting for webhooks in setup mode |
| `obdiv_batch_wait` | *(removed)* | No OBDIV phase |
| `cycle_interval` | `maintenance_interval` | For maintenance checks instead of cycles |
| *(new)* | `webhook_url` | Stock Buddy signal endpoint |
| *(new)* | `layout_name` | TradingView layout name |
| *(new)* | `alert_creation_delay` | Pause between batch alert creations |
| *(new)* | `screener_shorttitle` | Indicator legend name |
| *(new)* | `screener_name` | Indicator full name |

### Environment variables that need to be set

```bash
CHART_URL=https://www.tradingview.com/chart/XXXXXXX/   # TradingView chart with TTE Screener
WEBHOOK_URL=https://stock-buddy-app.vercel.app/api/tte/signal
STOCK_BUDDY_API_URL=https://stock-buddy-app.vercel.app/api/tte
```

---

## 4. Task 3: Rewrite api_client.py

### File: `api_client.py`

### Current State

Has tiered-specific methods: `get_next_symbol_batch()`, `mark_symbols_scanned()`, `get_hot_symbols()`, `delete_expired_hot_symbols()`.

### New API Client

Replace with combo-architecture methods. Keep `health_check()` and `get_stats()` as-is. Replace the tiered methods:

```python
"""
Stock Buddy API Client for TTE Combo Screener Orchestrator.

Handles communication with the Stock Buddy API for:
- Fetching the full symbol list for alert setup
- Tracking rotation/setup state
- Health checks and statistics
"""

import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class StockBuddyAPIClient:
    """Client for interacting with the Stock Buddy TTE API."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            health_url = self.base_url.replace("/api/tte", "/api/health")
            response = self.session.get(health_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_stats(self) -> Optional[Dict]:
        """Get system statistics."""
        try:
            response = self.session.get(
                f"{self.base_url}/stats", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return None

    def get_all_symbols(self) -> List[str]:
        """
        Fetch the complete list of symbols for alert setup.

        Returns:
            List of symbol strings (e.g., ["GBPAUD", "AUDJPY", ...])
            Empty list on error.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/symbols",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            symbols = data.get("symbols", [])
            symbol_strings = [
                s["symbol"] if isinstance(s, dict) else s for s in symbols
            ]
            logger.info(f"Fetched {len(symbol_strings)} symbols from API")
            return symbol_strings
        except Exception as e:
            logger.error(f"Failed to get symbols from API: {e}")
            return []

    def get_rotation_state(self) -> Optional[Dict]:
        """
        Get the current rotation/setup state.

        Returns:
            Dict with: batch_number, rotation_number, total_symbols, last_batch_at
            None on error.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/rotation-state",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get rotation state: {e}")
            return None

    def update_rotation_state(
        self, batch_number: int, symbols_in_batch: List[str]
    ) -> Dict:
        """
        Update the rotation state after creating a batch alert.

        Args:
            batch_number: The batch number just created
            symbols_in_batch: Symbols in this batch
        """
        try:
            response = self.session.post(
                f"{self.base_url}/rotation-state",
                json={"batch_number": batch_number, "symbols": symbols_in_batch},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Updated rotation state: batch #{batch_number}")
            return data
        except Exception as e:
            logger.error(f"Failed to update rotation state: {e}")
            return {"success": False, "error": str(e)}

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

### Methods removed vs added

| Removed | Reason |
|---------|--------|
| `get_next_symbol_batch()` | Replaced by `get_all_symbols()` — we get ALL symbols at once, not in rotating batches |
| `mark_symbols_scanned()` | No scanning/rotation — all alerts are created once |
| `get_hot_symbols()` | No two-tier filtering |
| `delete_expired_hot_symbols()` | No hot symbols concept |

| Added | Purpose |
|-------|---------|
| `get_all_symbols()` | Fetch the full ~1,054 symbol list for batch creation |
| `get_rotation_state()` | Check setup progress (which batch we're up to) |
| `update_rotation_state()` | Track progress as batches are created |

### Stock Buddy API endpoints needed

These endpoints need to exist on the Stock Buddy side:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/tte/symbols` | Returns `{ "symbols": ["GBPAUD", ...] }` |
| GET | `/api/tte/rotation-state` | Returns `{ "batch_number": N, ... }` |
| POST | `/api/tte/rotation-state` | Accepts `{ "batch_number": N, "symbols": [...] }` |
| POST | `/api/tte/signal` | Receives webhook from TradingView (already in the design) |
| GET | `/api/health` | Health check (already exists) |
| GET | `/api/tte/stats` | Statistics (already exists) |

---

## 5. Task 4: Rewrite orchestrator.py

### File: `orchestrator.py`

### Current State

`TieredOrchestrator` class with two-phase cycle: Phase 1 (NWE) + Phase 2 (OBDIV). Runs continuously, creating/deleting alerts each cycle.

### New Architecture

`ComboOrchestrator` class with two **separate modes** (not phases):
1. **Setup mode**: One-time creation of all ~264 alerts
2. **Maintenance mode**: Periodic check for stopped alerts

### Key Conceptual Difference

| Aspect | Old (Tiered) | New (Combo) |
|--------|-------------|-------------|
| Alerts | Created and deleted each cycle | Created once, persist forever |
| Lifecycle | Create → Wait → Delete → Repeat | Create all → Monitor for failures |
| Webhooks | Scrape alert log for detection | TradingView sends directly to Stock Buddy |
| Symbol processing | 20 at a time, rotating | All ~1,054 symbols covered simultaneously |
| Browser needed for | Every cycle | Only setup + maintenance |

### New Class Structure

```python
"""
TTE Combo Screener Orchestrator

Two modes:
1. Setup: Creates webhook alerts for all symbol batches (4 per alert)
2. Maintenance: Periodically checks for and restarts stopped alerts
"""

import logging
import time
from typing import List, Optional

from api_client import StockBuddyAPIClient
from config import Config

logger = logging.getLogger(__name__)

SCREENER_SHORTTITLE = "Screener"
SCREENER_NAME = "TTE Screener"
LAYOUT_NAME = "Screener"
SYMBOLS_PER_BATCH = 4


class ComboOrchestrator:

    def __init__(self, browser, api_client: StockBuddyAPIClient, config: Config):
        self.browser = browser
        self.api = api_client
        self.config = config
        self.running = False
        self._batches_created = 0
        self._total_batches = 0
        self._batch_symbol_map: dict[int, List[str]] = {}

    def setup_alerts(self, symbols: Optional[List[str]] = None, resume_from: int = 0) -> bool:
        """..."""
        # See detailed description below

    def run_maintenance(self):
        """..."""
        # See detailed description below

    def stop(self):
        self.running = False

    def _create_alert_for_batch(self, symbols: List[str], batch_num: int) -> bool:
        """..."""
        # See detailed description below

    def _input_symbols_to_screener(self, symbols: List[str]) -> bool:
        """..."""

    def _check_and_restart_stopped_alerts(self) -> int:
        """..."""

    def _find_stopped_alerts(self) -> List[dict]:
        """..."""

    def _delete_single_alert(self, alert_info: dict) -> bool:
        """..."""


def create_orchestrator(config: Optional[Config] = None) -> ComboOrchestrator:
    """Factory function — see detailed description below."""
```

### 5.1 `setup_alerts()` — Detailed Logic

```
def setup_alerts(symbols=None, resume_from=0):
    1. If symbols is None, call self.api.get_all_symbols()
    2. If no symbols returned, log error and return False
    3. Split symbols into batches of SYMBOLS_PER_BATCH (4)
       → batches = [symbols[i:i+4] for i in range(0, len(symbols), 4)]
    4. Set self._total_batches = len(batches)
    5. For each batch (starting from resume_from):
       a. Call self._create_alert_for_batch(batch, batch_num)
       b. If success: increment counter, store in batch_symbol_map,
          call self.api.update_rotation_state(batch_num, batch)
       c. If failure: log error, continue to next batch
       d. Sleep self.config.alert_creation_delay between batches
    6. Log summary: X/Y alerts created
    7. Return True if all succeeded
```

### 5.2 `_create_alert_for_batch()` — Detailed Logic

This reuses existing browser methods from `open_tv.py`:

```
def _create_alert_for_batch(symbols, batch_num):
    1. Call self._input_symbols_to_screener(symbols)
       → This calls self.browser.change_settings(symbols, screener_shorttitle)
       → change_settings already handles:
          - Stripping exchange prefixes ("OANDA:EURUSD" → "EURUSD")
          - Opening indicator settings dialog
          - Filling symbol inputs
          - Clicking Submit
    2. Sleep 3 seconds (screener recalculation time)
    3. Click on the screener indicator to select it:
       → indicator = self.browser._safe_indicator_access(screener_shorttitle)
       → indicator.click()
    4. Call self.browser.create_webhook_alert(screener_shorttitle, webhook_url)
       → create_webhook_alert already handles:
          - Opening alert dialog
          - Validating condition dropdown
          - Switching to Notifications tab
          - Enabling webhook checkbox
          - Filling webhook URL
          - Clicking Create
          - Checking for errors (data_subscription, condition_invalid)
    5. Return (success, error_type) from create_webhook_alert
```

### 5.3 `run_maintenance()` — Detailed Logic

```
def run_maintenance():
    1. Set self.running = True
    2. Loop while self.running:
       a. Call self._check_and_restart_stopped_alerts()
       b. Log count of restarted alerts
       c. Sleep self.config.maintenance_interval (default 30 min)
```

### 5.4 `_check_and_restart_stopped_alerts()` — Detailed Logic

```
def _check_and_restart_stopped_alerts():
    1. Open alerts sidebar: self.browser.open_alerts_sidebar()
    2. Open alerts tab: self.browser.utils.open_alert_tab(self.browser.driver)
    3. Find all alert items:
       → driver.find_elements(By.CSS_SELECTOR, "div.list-G90Hl2iS div.itemBody-ucBqatk5")
    4. For each alert item, check for stopped/error indicators:
       → item.find_elements(By.CSS_SELECTOR, ".statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS")
       → This is the SAME check used in open_tv.py's is_no_error() method
    5. For each stopped alert:
       a. Right-click to get context menu
       b. Click "Delete" option
       c. Confirm deletion
       d. Recreate with same symbols via _create_alert_for_batch()
    6. Return count of restarted alerts
```

**Note**: Identifying which symbols belong to a stopped alert is a challenge. Options:
- Store the batch-to-symbols mapping in the API (via `update_rotation_state`)
- Parse the alert name/description for symbol info
- Store the mapping locally in memory (lost on restart — least reliable)

### 5.5 `create_orchestrator()` — Factory Function

This replaces the existing `create_orchestrator()` function. Changes from current:

| Step | Old (Tiered) | New (Combo) |
|------|-------------|-------------|
| Config validation | Checks NWE + OBDIV chart URLs | Checks single chart_url + webhook_url |
| API startup cleanup | Deletes expired hot symbols | Nothing (no hot symbols) |
| Browser init | Uses NWE + OBDIV screener names | Uses single TTE Screener name |
| Navigation | Opens NWE chart URL | Opens single chart URL |
| Alert deletion at startup | Deletes all existing alerts | Does NOT delete alerts (they should persist!) |
| Layout verification | *(none)* | Verifies correct layout + indicator present |

**Critical difference**: The old factory deletes all alerts at startup (`browser.delete_all_alerts()`). The new one must NOT do this, because alerts are meant to persist. Only the `--setup` mode should optionally delete existing alerts before creating new ones.

```
def create_orchestrator(config=None):
    1. Load config (from param or default)
    2. Validate config
    3. Initialize StockBuddyAPIClient
    4. Check API health (non-blocking)
    5. Initialize Browser with:
       - screener_ob_short = config.screener_shorttitle  ("Screener")
       - screener_ob_name = config.screener_name  ("TTE Screener")
       - All other screener params = ""  (not used)
    6. Sign in to TradingView
    7. Navigate to config.chart_url
    8. Wait 5s for page load
    9. Verify layout matches config.layout_name
       → If not, call browser.change_layout(config.layout_name)
    10. Verify TTE Screener indicator is on the chart
        → browser._safe_indicator_access(config.screener_shorttitle)
    11. Open alerts sidebar
    12. Return ComboOrchestrator(browser, api_client, config)
```

### Existing `open_tv.py` methods used (no changes needed)

| Method | Used For |
|--------|----------|
| `Browser.__init__()` | Chrome initialization |
| `sign_in()` | TradingView authentication |
| `open_page(url)` | Navigate to chart |
| `change_layout(name)` | Switch TradingView layout |
| `current_layout()` | Verify current layout |
| `save_layout()` | Save layout state |
| `open_alerts_sidebar()` | Open alerts panel |
| `change_settings(symbols, shorttitle)` | Input symbols into screener settings |
| `create_webhook_alert(shorttitle, url)` | Create webhook alert with all the dialog automation |
| `_safe_indicator_access(shorttitle)` | Get indicator element safely |
| `_validate_alert_condition(popup, shorttitle)` | Check alert condition dropdown |
| `_close_alert_dialog()` | Close alert dialog on error |
| `delete_all_alerts()` | Only used in setup mode with --fresh flag |

---

## 6. Task 5: Create combo_main.py

### File: `combo_main.py` (NEW FILE)

### Purpose

CLI entry point for the combo screener orchestrator. Based on `tiered_main.py` but with different modes.

### CLI Arguments

```
python combo_main.py --setup              # Create all ~264 alerts (one-time)
python combo_main.py --setup --fresh      # Delete existing alerts first, then create all
python combo_main.py --setup --resume 50  # Resume setup from batch #50
python combo_main.py --maintain           # Run maintenance loop (check stopped alerts)
python combo_main.py --validate           # Validate configuration
python combo_main.py --test-api           # Test API connection
python combo_main.py --stats              # Show system statistics
```

### Structure

```python
#!/usr/bin/env python3
"""
TTE Combo Screener Orchestrator - Entry Point

Usage:
    python combo_main.py --setup              Create all alerts (one-time)
    python combo_main.py --setup --fresh      Delete existing alerts first
    python combo_main.py --setup --resume 50  Resume from batch #50
    python combo_main.py --maintain           Monitor and restart stopped alerts
    python combo_main.py --validate           Validate configuration
    python combo_main.py --test-api           Test API connection
    python combo_main.py --stats              Show system statistics
"""

import os
os.environ["SKIP_MONGODB_SYMBOLS"] = "true"  # Get symbols from API, not MongoDB

import argparse
import sys
import logging
import logger_setup
from config import config
from api_client import StockBuddyAPIClient

logger = logger_setup.setup_logger(__name__, logger_setup.INFO)


def validate_config() -> bool:
    """Validate and print config."""
    # Print all config fields, call config.validate(), show errors


def test_api() -> bool:
    """Test API connection."""
    # Health check, get stats, test get_all_symbols()


def show_stats():
    """Show system statistics."""
    # Fetch and display stats + rotation state


def run_setup(fresh: bool = False, resume_from: int = 0):
    """Run the setup phase to create all alerts."""
    from orchestrator import create_orchestrator

    orchestrator = create_orchestrator(config)

    if fresh:
        print("Deleting all existing alerts...")
        orchestrator.browser.delete_all_alerts()

    orchestrator.setup_alerts(resume_from=resume_from)


def run_maintenance():
    """Run the maintenance loop."""
    from orchestrator import create_orchestrator

    orchestrator = create_orchestrator(config)
    orchestrator.run_maintenance()


def main():
    parser = argparse.ArgumentParser(
        description="TTE Combo Screener Orchestrator"
    )
    parser.add_argument("--setup", action="store_true", help="Create all alerts")
    parser.add_argument("--fresh", action="store_true", help="Delete existing alerts before setup")
    parser.add_argument("--resume", type=int, default=0, help="Resume setup from batch N")
    parser.add_argument("--maintain", action="store_true", help="Run maintenance loop")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--test-api", action="store_true", help="Test API connection")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    if args.validate:
        sys.exit(0 if validate_config() else 1)
    if args.test_api:
        sys.exit(0 if test_api() else 1)
    if args.stats:
        show_stats()
        sys.exit(0)
    if args.setup:
        run_setup(fresh=args.fresh, resume_from=args.resume)
    elif args.maintain:
        run_maintenance()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Key difference from `tiered_main.py`

| Aspect | `tiered_main.py` | `combo_main.py` |
|--------|-------------------|-----------------|
| Default mode | Runs continuously (`run()`) | Requires explicit `--setup` or `--maintain` |
| Setup | Implicit (creates/deletes alerts each cycle) | Explicit `--setup` flag |
| Maintenance | *(none)* | Explicit `--maintain` flag |
| Resume | *(none)* | `--resume N` to continue from batch N |
| Fresh start | `--single-cycle` | `--fresh` deletes all alerts before setup |
| OBDIV testing | `--test-phase2` | *(removed)* |

---

## 7. Task 6: Update CLAUDE.md

### File: `CLAUDE.md`

### Changes

Update the following sections to reflect the combo architecture:

1. **Architecture Overview > Core Components**: Add ComboOrchestrator, update component list
2. **Tiered Architecture (New)** section: Rename to "Combo Screener Architecture" and update:
   - Key files: `combo_main.py`, `orchestrator.py` (ComboOrchestrator)
   - Remove references to NWE/OBDIV screeners
   - Update workflow description to single-screener model
3. **Running Tiered Mode**: Update to show `combo_main.py` commands
4. **TradingView Requirements > For Tiered Mode**: Update to single layout "Screener" with TTE Screener indicator
5. **Key Constants**: Update screener names and batch sizes

---

## 8. Dependencies Between Tasks

```
Task 1 (Pine Script) ─────────────────────────────────┐
                                                        │
Task 2 (config.py) ──────┐                             │
                          ├── Task 4 (orchestrator.py) ─┼── Task 5 (combo_main.py)
Task 3 (api_client.py) ──┘                             │
                                                        │
Task 6 (CLAUDE.md) ───────────────────────────────────┘
```

- Tasks 1, 2, 3, 6 are **fully independent** — can be done in any order or in parallel
- Task 4 **requires** Tasks 2 and 3 (imports Config and StockBuddyAPIClient)
- Task 5 **requires** Task 4 (imports create_orchestrator and ComboOrchestrator)

---

## 9. What NOT to Change

These files should NOT be modified:

| File | Reason |
|------|--------|
| `open_tv.py` | All browser automation methods work as-is. The combo orchestrator calls them with different parameters but the code is unchanged. |
| `handle_alerts.py` | Legacy system — not used by combo architecture but kept for backwards compatibility |
| `env.py` | Environment config unchanged |
| `resources/symbol_settings.py` | Symbol loading unchanged (combo uses `SKIP_MONGODB_SYMBOLS=true`) |
| `database/` | Database modules unchanged |
| `main.py` | Legacy entry point — kept for backwards compatibility |
| `gui.py` | GUI unchanged |
| `send_to_socials/` | Social distributors unchanged |
| `resources/utils.py` | Utility functions used by open_tv.py unchanged |
| `open_entry_chart.py` | Chart automation used by open_tv.py unchanged |
| `logger_setup.py` | Logging unchanged |
| `exits.py` | Exit monitoring unchanged |

### Files that will be superseded but NOT deleted

| File | Status |
|------|--------|
| `tiered_main.py` | Superseded by `combo_main.py`. Keep for reference. |

The old `tiered_main.py` should remain in the repo but is no longer the active entry point. The new entry point is `combo_main.py`.
