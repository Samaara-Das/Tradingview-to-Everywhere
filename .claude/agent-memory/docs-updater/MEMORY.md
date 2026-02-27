# Docs Updater Agent Memory

## Key Architecture Facts (V2 — Feb 2026)

- **Chart timeframe**: 45 seconds (yaml) — NOT 30 seconds. Always verify against `combo_settings.yaml`.
- **Batch size**: 2 symbols per alert (not 3 as in V1)
- **Total alerts**: ~314 (not 338 V1)
- **Total symbols**: 626 (not 1028 V1)
- **Maintenance interval**: 150s / 2.5 min (not 300s / 5 min)
- **Alert frequency**: `alert.freq_once_per_bar_close` (not `alert.freq_all`)
- **Divergence**: Removed in V2. No divergence signals or payload fields.
- **Payload format**: Compact abbreviated keys (`ts`, `s`, `sym`, `nwe`, `ob`, `b`, `se`)
- **Category-aware pairing**: Symbols paired within same asset class in `fetch_symbols_by_category()`

## Common Stale Doc Patterns

- SETUP.md tends to reference V1 chart settings (1-min timeframe, line bar style, "TTE Screener")
- PRD.md had V1 production config table with stale numbers
- ARCHITECTURE.md system overview diagram had V1 symbol/alert counts
- Section 5 (Pine Script) in ARCHITECTURE.md kept V1 divergence and `freq_all` details
- API.md combo section showed V1 verbose payload format

## Source-of-Truth Files (always read before updating docs)

- `combo_settings.yaml` — actual runtime defaults (more accurate than code defaults in config.py)
- `tte/config.py` — code defaults (fallback if yaml key missing)
- `Pine Script Code/TTE Screener V2.txt` — V2 indicator (active)
- `Pine Script Code/TTE Screener.txt` — V1 indicator (archived)
- `tte/main.py` — orchestrator logic and `fetch_symbols_by_category()`

## Docs that Are Accurate (as of Feb 2026)

- `CLAUDE.md` — updated to V2
- `README.md` — already accurate for V2
- `docs/combo/ARCHITECTURE.md` V2 section at top — accurate
- `docs/combo/IMPLEMENTATION.md` — archived, no updates needed

## Snapshot Worker (new in PR #7)

- File: `tte/snapshot_worker.py`
- Polls every 60s, processes up to 5 pending snapshots per batch
- Uses separate "Snapshot" TradingView layout with NWE + Trade Drawer v2
- Maintenance (150s) has priority over snapshots when both timers fire
- GUI exposes snapshot settings (enabled, layout, bar style, batch size, poll interval, bars_to_right)

## Git/Branch Workflow

- Always make doc updates on a dedicated branch, never directly to main
- Current doc update branch: `docs/update-for-v2-architecture`
