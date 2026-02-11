# System Architecture

Technical architecture documentation for TradingView to Everywhere (TTE).

## Overview

TTE is a browser automation system that bridges TradingView alerts with external platforms. It operates in two modes: Legacy (poll-based) and Tiered (webhook-based).

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TTE System Architecture                          │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  TradingView │
                              │   (Browser)  │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │  Legacy   │    │  Tiered   │    │    GUI    │
            │  Mode     │    │   Mode    │    │   Mode    │
            │ (main.py) │    │(tiered_   │    │ (gui.py)  │
            └─────┬─────┘    │ main.py)  │    └─────┬─────┘
                  │          └─────┬─────┘          │
                  │                │                │
                  └────────────────┼────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐
            │  Browser  │  │    API    │  │  MongoDB  │
            │ Controller│  │   Client  │  │  Database │
            │(open_tv.py│  │(api_client│  │(local_db  │
            └───────────┘  │   .py)    │  │   .py)    │
                           └─────┬─────┘  └───────────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │  Stock Buddy  │
                         │     API       │
                         └───────────────┘
```

---

## Data Flow Diagrams

### Legacy Mode Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Legacy Mode Data Flow                             │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐     ┌──────────────┐     ┌───────────────┐
    │TradingView│────▶│ Alert Handler │────▶│ Chart Manager │
    │  Alerts  │     │(handle_alerts)│     │(open_entry_   │
    └──────────┘     └──────────────┘     │   chart)      │
                                          └───────┬───────┘
                                                  │
                                                  ▼
                                          ┌───────────────┐
                                          │  Screenshot   │
                                          │   Capture     │
                                          └───────┬───────┘
                                                  │
                      ┌───────────────────────────┼───────────────────────┐
                      │                           │                       │
                      ▼                           ▼                       ▼
               ┌───────────┐              ┌───────────┐           ┌───────────┐
               │  Discord  │              │  Twitter  │           │  MongoDB  │
               │ (webhook) │              │   (API)   │           │           │
               └───────────┘              └───────────┘           └───────────┘
```

### Tiered Mode Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Tiered Mode Data Flow                             │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │ Stock Buddy  │◀────── Get symbol batch
    │     API      │
    └──────┬───────┘
           │
           ▼ symbols
    ┌──────────────┐
    │ Orchestrator │
    │(orchestrator │
    │    .py)      │
    └──────┬───────┘
           │
           ├──────────────────────────────────────┐
           │                                      │
           ▼ Phase 1                              ▼ Phase 2
    ┌──────────────┐                      ┌──────────────┐
    │ NWE Screener │                      │OBDIV Screener│
    │  (TV Layout) │                      │  (TV Layout) │
    └──────┬───────┘                      └──────┬───────┘
           │                                      │
           ▼ webhook                              ▼ webhook
    ┌──────────────┐                      ┌──────────────┐
    │ /api/tte/nwe │                      │/api/tte/obdiv│
    │   endpoint   │                      │   endpoint   │
    └──────┬───────┘                      └──────────────┘
           │
           ▼ hot symbols
    ┌──────────────┐
    │ Hot Symbols  │────────────────────▶ Phase 2
    │    Queue     │
    └──────────────┘
```

---

## Module Reference

### Core Modules

#### `open_tv.py` - Browser Controller

Main browser automation module for TradingView interaction.

**Key Class**: `Browser`

**Responsibilities**:
- Chrome WebDriver initialization and management
- TradingView authentication
- Layout switching and management
- Indicator interaction
- Alert creation and deletion
- Symbol settings input

**Key Methods**:
| Method | Description |
|--------|-------------|
| `sign_in()` | Authenticate with TradingView |
| `open_page(url)` | Navigate to URL and maximize window |
| `setup_tv()` | Initialize TradingView for legacy mode |
| `change_layout(name)` | Switch to named layout |
| `save_layout()` | Save current layout state |
| `change_settings(symbols, screener)` | Input symbols into screener |
| `set_alerts(symbols, screener)` | Create alerts for screener |
| `create_webhook_alert(indicator, url)` | Create webhook alert |
| `delete_all_alerts()` | Remove all existing alerts |
| `indicator_visibility(visible, name)` | Show/hide indicator |
| `get_indicator(name)` | Find indicator by short title |

#### `orchestrator.py` - Tiered Orchestrator

Manages the two-tier symbol scanning workflow.

**Key Class**: `TieredOrchestrator`

**Responsibilities**:
- Coordinate NWE (Tier 1) and OBDIV (Tier 2) phases
- Manage API communication
- Handle layout switching
- Track batch progress

**Key Methods**:
| Method | Description |
|--------|-------------|
| `run(single_cycle)` | Start orchestration loop |
| `stop()` | Gracefully stop orchestrator |
| `_phase1_nwe_batch()` | Execute NWE phase |
| `_phase2_obdiv_processing()` | Execute OBDIV phase |
| `_input_symbols_to_screener()` | Input symbols to screener |
| `_switch_to_layout_with_setup()` | Switch layout with initialization |

**Factory Function**: `create_orchestrator(config)` - Creates fully initialized orchestrator

#### `api_client.py` - Stock Buddy API Client

HTTP client for Stock Buddy API communication.

**Key Class**: `StockBuddyAPIClient`

**Key Methods**:
| Method | Description |
|--------|-------------|
| `health_check()` | Verify API availability |
| `get_stats()` | Get system statistics |
| `get_next_symbol_batch(size)` | Fetch next symbol batch |
| `mark_symbols_scanned(symbols)` | Mark symbols as scanned |
| `get_hot_symbols(limit)` | Get hot symbols for OBDIV |

#### `config.py` - Configuration Management

Centralized configuration from environment variables.

**Key Class**: `Config` (dataclass)

**Configuration Fields**:
| Field | Default | Description |
|-------|---------|-------------|
| `api_base_url` | Stock Buddy URL | API endpoint |
| `api_timeout` | 30 | Request timeout (seconds) |
| `nwe_chart_url` | Required | NWE layout chart URL |
| `obdiv_chart_url` | Required | OBDIV layout chart URL |
| `nwe_batch_size` | 20 | Symbols per NWE batch |
| `obdiv_batch_size` | 8 | Symbols per OBDIV batch |
| `nwe_batch_wait` | 60 | Wait after NWE alert (seconds) |
| `obdiv_batch_wait` | 60 | Wait after OBDIV alert (seconds) |
| `cycle_interval` | 300 | Wait between cycles (seconds) |

### Supporting Modules

#### `handle_alerts.py` - Alert Processing

Processes alert messages and extracts trade information.

**Key Class**: `Alerts`

#### `open_entry_chart.py` - Chart Navigation

Navigates charts and manages timeframes.

**Key Class**: `OpenChart`

**Key Methods**:
| Method | Description |
|--------|-------------|
| `change_symbol(symbol)` | Change chart symbol |
| `change_tframe(timeframe)` | Change timeframe |
| `force_change_tframe(timeframe)` | Force timeframe change |

#### `exits.py` - Exit Monitoring

Tracks trade exits and distributes exit notifications.

#### `database/local_db.py` - MongoDB Operations

MongoDB database operations and connection management.

**Key Class**: `Database`

#### `resources/symbol_settings.py` - Symbol Management

Symbol definitions, categories, and batch management.

**Key Functions**:
| Function | Description |
|----------|-------------|
| `get_symbols()` | Get all symbols from MongoDB |
| `get_symbol_categories()` | Get symbol-to-category mapping |
| `fill_symbol_set(size)` | Batch symbols into groups |
| `symbol_category(symbol)` | Get category for symbol |

#### `resources/utils.py` - Utility Functions

Shared utility functions for browser automation.

**Key Class**: `Utils`

**Key Methods**:
| Method | Description |
|--------|-------------|
| `open_alert_tab(driver)` | Open alerts sidebar tab |
| `click_yes_in_confirm_popup(driver)` | Confirm popup dialogs |

---

## Selenium Selectors Reference

Critical CSS selectors and XPaths used for TradingView automation:

### Layout Elements

```python
# Layout dropdown button
'//*[@id="header-toolbar-save-load"]'

# Layout dropdown arrow
'/html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/div/button'

# Layout list items
'//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/a'

# Layout title text
'.layoutTitle-yyMUOAN9'

# Current layout text
'.text-yyMUOAN9'

# Save indicator
'.saveString-XVd1Kfjg'
```

### Indicator Elements

```python
# Indicator container
'div[data-qa-id="legend-source-item"]'
'div[data-name="legend-source-item"]'

# Indicator title
'div[class="title-l31H9iuA"]'

# Settings button
'button[data-qa-id="legend-settings-action"]'

# Delete button
'button[data-name="legend-delete-action"]'

# Visibility button
'button[data-name="legend-show-hide-action"]'

# Error indicator
'.statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS'
```

### Alert Elements

```python
# Alerts sidebar button
'div[data-name="right-toolbar"] button[aria-label="Alerts"]'

# Set alert button
'div[data-name="set-alert-button"]'

# Alert dialog
'div[data-qa-id="alerts-create-edit-dialog"]'

# Submit button
'button[data-qa-id="submit"]'

# Cancel button
'button[data-qa-id="cancel"]'

# Close button
'button[data-name="close"]'

# Error hint
'div[data-name="error-hint"]'

# Alert items
'div.list-G90Hl2iS div.itemBody-ucBqatk5'

# Settings button (3 dots)
'div[data-name="alerts-settings-button"]'

# Dropdown menu
'div[data-qa-id="menu-inner"]'
'div[data-name="menu-inner"]'

# Dropdown items
'div.item-jFqVJoPk'
```

### Webhook Alert Elements

```python
# Notifications tab
'button[id="alert-dialog-tabs__notifications"]'

# Webhook checkbox
'input[data-qa-id="webhook"]'

# Webhook URL input
'input#webhook-url'
```

### Settings Dialog Elements

```python
# Settings modal content
'.content-tBgV1m0B'

# Settings dialog container
'div[data-outside-boundary-for="indicator-properties-dialog"]'

# Symbol inputs
'.inlineRow-uuCuCMOL div[data-name="edit-button"]'

# Timeframe inputs
'div[class="cell-tBgV1m0B"] input'

# Submit button
'button[name="submit"]'

# Symbol search input
'//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input'
```

### Timeframe Elements

```python
# Timeframe button
'//*[@id="header-toolbar-intervals"]/button'

# Timeframe menu
'div[data-name="menu-inner"]'

# Timeframe items
'div[data-role="menuitem"]'
```

### Chart Style Elements

```python
# Candle style button
'div[id="header-toolbar-chart-styles"] button'
```

### Authentication Elements

```python
# Products menu (indicates logged in)
'a[data-main-menu-root-track-id="products"]'

# Email login button
'name="Email"'

# Username input
'name="id_username"'

# Password input
'name="id_password"'

# Sign in button
'button[data-overflow-tooltip-text="Sign in"]'
```

### Indicator Favorites

```python
# Favorites dropdown button
'div[id="header-toolbar-indicators"] button[data-name="show-favorite-indicators"]'

# Indicator label in dropdown
'span[class="label-l0nf43ai apply-overflow-tooltip"]'
```

---

## Configuration Constants

### `open_tv.py`

```python
SYMBOL_INPUTS = 5              # Number of symbol inputs in screener
CHART_TIMEFRAME = "5 minutes"  # Chart timeframe for entries
USED_SYMBOLS_INPUT = "Used Symbols"
LAYOUT_NAME = "PointCapital"   # Default layout for legacy mode
SCREENER_REUPLOAD_TIMEOUT = 15 # Seconds to wait for indicator reupload
```

### `orchestrator.py`

```python
# Screener names
NWE_SCREENER_SHORTTITLE = "TTE NWE Screener"
NWE_SCREENER_NAME = "TTE NWE Screener"
OBDIV_SCREENER_SHORTTITLE = "TTE OBDIV Screener"
OBDIV_SCREENER_NAME = "TTE OBDIV Screener"

# Layout names
NWE_LAYOUT_NAME = "NWE"
OBDIV_LAYOUT_NAME = "OBDIV"

# Webhook paths
NWE_WEBHOOK_PATH = "/nwe"
OBDIV_WEBHOOK_PATH = "/obdiv"
```

---

## Error Handling Patterns

### Stale Element Recovery

```python
def _safe_indicator_access(self, shorttitle: str, max_retries: int = 2):
    """Safely access an indicator with retry logic for stale element exceptions"""
    for attempt in range(max_retries):
        try:
            indicator = self._get_fresh_indicator(shorttitle)
            if indicator:
                _ = indicator.get_attribute("class")  # Test validity
                return indicator
        except StaleElementReferenceException:
            if attempt < max_retries - 1:
                sleep(1)
    return None
```

### Layout Switching with Retry

```python
def _switch_to_layout_with_setup(self, layout_name, is_first_switch):
    result = self.browser.change_layout(layout_name)
    if not result:
        self.browser.change_layout(layout_name)  # Retry
        current = self.browser.current_layout()
        if current != layout_name:
            return False
    time.sleep(5)  # Wait for layout to load
    return True
```

---

## See Also

- [API Reference](API.md) - Stock Buddy API details
- [Database](DATABASE.md) - MongoDB schema
- [Setup Guide](SETUP.md) - Installation and configuration
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
