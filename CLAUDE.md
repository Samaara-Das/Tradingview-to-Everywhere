# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingView to Everywhere (TTE) is an automated trading signals distribution system that bridges TradingView alerts with multiple platforms. It uses Selenium browser automation to interact with TradingView and webhooks to distribute signals to Stock Buddy API.

### Critical Principles
1. **Reuse existing code**: Before implementing anything, check if it already exists in the codebase
2. **Three operational modes**: Legacy (poll-based), Tiered (two-phase webhook), Combo (single-indicator webhook)
3. **Never modify `open_tv.py`**: All browser automation is reusable with different parameters

## Three Operational Modes

### 1. Legacy Mode (`main.py`)
- **Method**: Poll-based alert scraping with Selenium
- **Use case**: Screenshot capture + social distribution
- **Key files**: `main.py`, `handle_alerts.py`, `exits.py`

### 2. Tiered Mode (`tiered_main.py`)
- **Method**: Two-phase webhook filtering (NWE → OBDIV)
- **Workflow**: 20 symbols (NWE) → hot symbols → 8 symbols (OBDIV)
- **Alert lifecycle**: Create → wait → delete → repeat
- **Key files**: `tiered_main.py`, `orchestrator.py`, `api_client.py`, `config.py`
- **Docs**: `docs/PRD.md`

### 3. Combo Mode (`combo_main.py`) - **IN PLANNING**
- **Method**: Single combo screener (NWE + OB/FVG + Divergence)
- **Workflow**: 264 persistent alerts (4 symbols each) → webhook continuously
- **Alert lifecycle**: Create once → run forever (+ maintenance every 5 mins)
- **Key difference**: 4-symbol hard limit (more causes TradingView errors)
- **Docs**: `docs/ARCHITECTURE v2.md`, `docs/COMBO_IMPLEMENTATION.md`

## Running Commands

```bash
pipenv shell                       # Activate environment
python main.py                     # Legacy mode
python tiered_main.py              # Tiered mode
python combo_main.py               # Combo mode (after implementation)
```

## Core Architecture Concepts

### Browser Automation (`open_tv.py`)
- **DO NOT MODIFY**: All methods are reusable with different parameters
- Manages all Selenium interactions with TradingView
- Key pattern: `_safe_indicator_access()` handles stale elements with retry logic

### Alert Lifecycles

| Mode | Create | Monitor | Delete | Timeframe |
|------|--------|---------|--------|-----------|
| Legacy | At startup | Poll alert log | Manual/restart | Continuous |
| Tiered | Per batch | Webhook wait | After trigger | ~90s per batch |
| Combo | Once (264 alerts) | TradingView servers | Never (persist) | One-time setup |

### Combo Mode Critical Details
- **4-symbol hard limit**: More causes TradingView memory/runtime errors
- **264 persistent alerts**: ~1,054 symbols ÷ 4 = 264 alerts
- **Timeframe mismatch**: Variable names (TF_H4/TF_D1/TF_W1) are legacy; production is 1H/H4/D1
- **Parallel setup**: Use 4 browser tabs to reduce setup from 6.6h → 1.6h
- **Maintenance**: Every 5 mins, call `restart_inactive_alerts()` from `handle_alerts.py:240-303`

## Configuration Essentials

### TradingView Requirements (All Modes)
- **2FA**: Must be disabled
- **Social accounts**: None linked
- **Subscription**: Premium (for webhooks in Tiered/Combo)
- **Layouts**: Mode-specific (Legacy: "Screener"+"Exits", Tiered: "NWE"+"OBDIV", Combo: "Screener")
- **Indicators**: Must be starred/favorited

### Environment Variables
See `env.py` and `.env` file. Key variables: `CHROME_PROFILES_PATH`, `TRADINGVIEW_EMAIL`, `TRADINGVIEW_PASSWORD`, `MONGODB_PWD`

## Critical Constants

| Constant | Legacy | Tiered | Combo |
|----------|--------|--------|-------|
| Batch size | 5 symbols | 20 (NWE), 8 (OBDIV) | **4 (hard limit)** |
| Restart interval | 10 mins | N/A | 5 mins |
| Alert lifecycle | Create at startup | Create/delete cycle | Create once + maintain |

**Combo Pine Script Timeframes** (production values):
- `TF_H4="60"` (1H), `TF_D1="240"` (H4), `TF_W1="D"` (D1) — variable names are legacy

## Development Guidelines

1. **Reuse existing code**: Check before implementing — patterns for alerts, tabs, indicators already exist
2. **Always log**: Use `print(..., flush=True)` or `logger.info/debug/error()` in every significant code block
3. **Never modify `open_tv.py`**: All browser automation is reusable with parameters
4. **Document mistakes**: Write learnings to `AGENTS.md` to prevent repetition
5. **Use built-in task management**: Always use TaskCreate/TaskUpdate/TaskList tools (NOT MCP task-master-ai) for tracking work

## Key Reusable Code Locations

| What | Where | Use Case |
|------|-------|----------|
| Restart inactive alerts | `handle_alerts.py:240-303` | Combo maintenance (every 5 mins) |
| Tab switching | `open_entry_chart.py:277-318` | Parallel alert creation (combo setup) |
| Create webhook alert | `open_tv.py:1007-1361` | All webhook modes |
| Delete all alerts | `open_tv.py:1502-1627` | Tiered mode only (NOT combo) |
| Safe element access | `open_tv.py:1757-1780` | When Selenium elements go stale |


## Documentation

| Change Type | Update |
|-------------|--------|
| Architecture/workflow | `docs/ARCHITECTURE.md` (tiered), `docs/ARCHITECTURE v2.md` (combo) |
| Implementation tasks | `docs/PRD.md` (tiered), `docs/COMBO_IMPLEMENTATION.md` (combo) |
| Other changes | `README.md`, `docs/SETUP.md`, `docs/API.md`, etc. |

Update docs in the same PR as code changes.