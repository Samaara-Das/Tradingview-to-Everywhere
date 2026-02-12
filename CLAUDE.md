# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with Stock Buddy API. It uses Selenium browser automation to interact with TradingView and webhooks to distribute signals.

### Critical Principles
1. **Reuse existing code**: Before implementing anything, check if it already exists in the codebase
2. **Changes to `open_tv.py` should be tested carefully**: It contains all browser automation logic
3. **Use built-in task management**: Always use TaskCreate/TaskUpdate/TaskList tools for tracking work

## Combo Mode (`combo_main.py`) — Production

- **Method**: Single combo screener (NWE + OB/FVG + Divergence) with persistent webhook alerts
- **Workflow**: ~352 persistent alerts (3 symbols each) → webhook continuously to Stock Buddy API
- **Alert lifecycle**: Create once → run forever (+ maintenance every 5 mins)
- **4-symbol hard limit**: More causes TradingView memory/runtime errors (using 3 in production)
- **Single browser**: Alerts created sequentially with one Chrome instance (headless by default)
- **Chart**: 1-minute timeframe, line bar style (for minimal resource usage)
- **Key files**: `combo_main.py`, `combo_config.py`, `combo_settings.yaml`
- **Docs**: `docs/combo/ARCHITECTURE.md`, `docs/combo/PRD.md`

## Running Commands

```bash
pipenv shell                              # Activate environment
python combo_main.py                      # Full setup + maintenance
python combo_main.py --setup-only         # Create alerts, then exit
python combo_main.py --maintain-only      # Skip setup, run maintenance only
python combo_main.py --fresh              # Delete all existing alerts before setup
python combo_main.py --validate           # Validate config and exit
python tte_gui.py                         # GUI interface
```

## Core Architecture

### Browser Automation (`open_tv.py`)
- Manages all Selenium interactions with TradingView
- Key pattern: `_safe_indicator_access()` handles stale elements with retry logic
- `create_webhook_alert()` creates alerts with webhook notification
- `reupload_indicator()` recovers from screener errors
- `change_settings()` fills in symbol inputs for the screener

### Settings (`combo_settings.yaml`)
All combo mode options are configured in `combo_settings.yaml`. Secrets (webhook URL) are in `.env`.

| Setting | YAML Path | Default | Description |
|---------|-----------|---------|-------------|
| Layout | `chart.layout_name` | "Screener" | TradingView layout name |
| Timeframe | `chart.chart_timeframe` | "1 minute" | Chart timeframe (must match dropdown label) |
| Bar style | `chart.bar_style` | "line" | Chart bar style data-value (candle, line, ha, etc.) |
| Screener | `screener.shorttitle` | "Screener" | Indicator short title on chart |
| Batch size | `alerts.batch_size` | 3 | Symbols per alert (hard limit) |
| Creation delay | `alerts.creation_delay` | 1.5 | Seconds between batches |
| Maintenance | `maintenance.interval` | 300 | Seconds between restart cycles |

### Environment Variables
See `env.py` and `.env` file. Key variables: `CHROME_PROFILES_PATH`, `TRADINGVIEW_EMAIL`, `TRADINGVIEW_PASSWORD`, `MONGODB_PWD`, `COMBO_WEBHOOK_URL`

### TradingView Requirements
- **2FA**: Must be disabled
- **Social accounts**: None linked
- **Subscription**: Premium (for webhooks)
- **Layout**: "Screener" with the combo indicator starred/favorited

## Development Guidelines

1. **Reuse existing code**: Check before implementing — patterns for alerts, tabs, indicators already exist
2. **Always log**: Use `logger.info/debug/error()` in every significant code block
3. **Test `open_tv.py` changes carefully**: Browser automation is fragile; verify with a real browser
4. **Document mistakes**: Write learnings to `AGENTS.md` to prevent repetition

## Key Code Locations

| What | Where | Use Case |
|------|-------|----------|
| Restart inactive alerts | `combo_main.py:366-438` | Maintenance (every 5 mins) |
| Create webhook alert | `open_tv.py` `create_webhook_alert()` | Alert creation |
| Change screener settings | `open_tv.py` `change_settings()` | Symbol configuration |
| Safe element access | `open_tv.py` `_safe_indicator_access()` | When Selenium elements go stale |
| Re-upload indicator | `open_tv.py` `reupload_indicator()` | Screener error recovery |

## Documentation

| Change Type | Update |
|-------------|--------|
| Architecture/workflow | `docs/combo/ARCHITECTURE.md` |
| Implementation tasks | `docs/combo/PRD.md` |
| Other changes | `README.md`, `docs/SETUP.md`, `docs/API.md`, etc. |

Update docs in the same PR as code changes.
