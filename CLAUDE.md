# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with Stock Buddy API. It uses Selenium browser automation to interact with TradingView and webhooks to distribute signals.

### Critical Principles
1. **Reuse existing code**: Before implementing anything, check if it already exists in the codebase
2. **Changes to `tte/browser/tradingview.py` should be tested carefully**: It contains all browser automation logic
3. **Use built-in task management**: Always use TaskCreate/TaskUpdate/TaskList tools for tracking work

## Combo Mode (`tte/main.py`) — Production

- **Method**: Single combo screener (NWE + OB/FVG, stateless setup detection) with persistent webhook alerts
- **Workflow**: ~310 persistent alerts (2 symbols each, category-aware pairing) → webhook every 45s to Stock Buddy API
- **Alert lifecycle**: Create once → run forever (+ maintenance every 2.5 mins)
- **Screener V2**: Stateless setup detection (NWE + OB/FVG alignment). Exit detection handled by Stock Buddy cron (every 5 min via Binance/Yahoo candles)
- **Single browser**: Alerts created sequentially with one Chrome instance (headless by default)
- **Chart**: 45-second timeframe, candle bar style, `alert.freq_once_per_bar_close`
- **Key files**: `tte/main.py`, `tte/config.py`, `combo_settings.yaml`, `Pine Script Code/TTE Screener V2.txt`
- **Docs**: `docs/combo/ARCHITECTURE.md`, `docs/combo/PRD.md`

## Running Commands

```bash
pipenv shell                              # Activate environment
python combo_main.py                      # Full setup + maintenance (shim)
python -m tte.main                        # Full setup + maintenance (direct)
python combo_main.py --setup-only         # Create alerts, then exit
python combo_main.py --maintain-only      # Skip setup, run maintenance only
python combo_main.py --fresh              # Delete all existing alerts before setup
python combo_main.py --validate           # Validate config and exit
python combo_main.py --symbols EURUSD,GBPUSD  # Test with specific symbols only
python tte_gui.py                         # GUI interface
```

## Core Architecture

### Package Structure (`tte/`)
- `tte/main.py` — Entry point (orchestrator)
- `tte/config.py` — Configuration loader + PROFILE constant
- `tte/log.py` — Logger setup (named `log` to avoid shadowing stdlib `logging`)
- `tte/snapshot_worker.py` — Chart snapshot polling & browser orchestration
- `tte/browser/tradingview.py` — TradingView browser automation (Selenium)
- `tte/browser/chart.py` — Chart navigation (timeframe collapsible sections, symbol search)
- `tte/browser/helpers.py` — Selenium utility functions
- `tte/data/symbols.py` — MongoDB symbol fetching

### Browser Automation (`tte/browser/tradingview.py`)
- Manages all Selenium interactions with TradingView
- Key pattern: `_safe_indicator_access()` handles stale elements with retry logic
- `create_webhook_alert()` creates alerts via two-dialog flow (main dialog + webhook notifications sub-dialog)
- `reupload_indicator()` recovers from screener errors
- `change_settings()` fills in symbol inputs for the screener
- `change_layout()` switches layouts via scoped XPath + href navigation for non-current layouts
- `_validate_alert_condition()` validates the condition dropdown shows the screener (not "Price")

### Settings (`combo_settings.yaml`)
All combo mode options are configured in `combo_settings.yaml`. Secrets (webhook URL) are in `.env`.

| Setting | YAML Path | Default | Description |
|---------|-----------|---------|-------------|
| Layout | `chart.layout_name` | "Screener" | TradingView layout name |
| Timeframe | `chart.chart_timeframe` | "45 seconds" | Chart timeframe (must match dropdown label) |
| Bar style | `chart.bar_style` | "candle" | Chart bar style data-value (candle, line, ha, etc.) |
| Screener | `screener.shorttitle` | "Screener V2" | Indicator short title on chart |
| Batch size | `alerts.batch_size` | 2 | Symbols per alert (category-aware pairing) |
| Creation delay | `alerts.creation_delay` | 1.5 | Seconds between batches |
| Maintenance | `maintenance.interval` | 150 | Seconds between restart cycles |
| Snapshot enabled | `snapshot.enabled` | true | Enable chart snapshot worker |
| Snapshot layout | `snapshot.layout_name` | "Snapshot" | TradingView layout for snapshots |
| Snapshot bar style | `snapshot.bar_style` | "candle" | Bar style for snapshot charts |
| Snapshot batch size | `snapshot.batch_size` | 10 | Pending snapshots per poll |
| Snapshot poll interval | `snapshot.poll_interval` | 60 | Seconds between snapshot polls |
| Snapshot bars right | `snapshot.bars_to_right` | 60 | Right margin bars for chart framing |

### Environment Variables
See `tte/config.py` and `.env` file. Key variables: `CHROME_PROFILES_PATH`, `TRADINGVIEW_EMAIL`, `TRADINGVIEW_PASSWORD`, `MONGODB_PWD`, `COMBO_WEBHOOK_URL`

### TradingView Requirements
- **2FA**: Must be disabled
- **Social accounts**: None linked
- **Subscription**: Premium (for webhooks)
- **Layout**: "Screener" with the combo indicator starred/favorited

## Development Guidelines

1. **Reuse existing code**: Check before implementing — patterns for alerts, tabs, indicators already exist
2. **Always log**: Use `logger.info/debug/error()` in every significant code block
3. **Test `tte/browser/tradingview.py` changes carefully**: Browser automation is fragile; verify with a real browser
4. **TradingView UI changes frequently**: Always use `data-qa-id` selectors (stable) over dynamic class names

## Key Code Locations

| What | Where | Use Case |
|------|-------|----------|
| Restart inactive alerts | `tte/main.py` `restart_inactive_alerts()` | Maintenance (every 2.5 mins) |
| Create webhook alert | `tte/browser/tradingview.py` `create_webhook_alert()` | Alert creation (two-dialog flow) |
| Change screener settings | `tte/browser/tradingview.py` `change_settings()` | Symbol configuration |
| Safe element access | `tte/browser/tradingview.py` `_safe_indicator_access()` | When Selenium elements go stale |
| Re-upload indicator | `tte/browser/tradingview.py` `reupload_indicator()` | Screener error recovery |
| Change timeframe | `tte/browser/chart.py` `change_tframe()` | Timeframe with collapsible section support |
| Switch layout | `tte/browser/tradingview.py` `change_layout()` | Layout switch via href navigation |
| Chart snapshots | `tte/snapshot_worker.py` `SnapshotWorker` | Async chart screenshots for setups |
| Auto-retry failed batches | `tte/main.py` `run_alert_creation()` | Retry once after initial failures |

## Documentation

| Change Type | Update |
|-------------|--------|
| Architecture/workflow | `docs/combo/ARCHITECTURE.md` |
| Implementation tasks | `docs/combo/PRD.md` |
| Other changes | `README.md`, `docs/SETUP.md`, `docs/API.md`, etc. |

Update docs in the same PR as code changes.
