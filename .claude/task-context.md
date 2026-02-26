# Task Context Tracker

**Last Updated**: 2026-02-26
**Current Task**: V2 implementation complete, PR open. Next: testing & deployment.
**Active Branch**: `feat/screener-v2` → **PR #8** (https://github.com/Samaara-Das/Tradingview-to-Everywhere/pull/8)
**Latest Commit (TTE)**: `4f7d0ab` — TTE Screener V2: setup/exit tracking in Pine Script
**Latest Commit (Stock Buddy)**: `bc0b810` — Add snapshot backfill endpoint

---

## Task Progress Summary

| # | Task | Status |
|---|------|--------|
| 131–144 | Chart snapshots feature + backfill | completed |
| 145 | Understand snapshot processing timing and batch size | completed |
| 147 | Decide on testing strategy (TDD / test coverage) | pending |
| 148 | Set up pre-commit hooks for linting, type checking, and formatting | completed |
| 149 | Rebuild and redeploy TTE.exe | completed |

### V2 Architecture Shift — Implementation (All Complete)

| # | Task | Status |
|---|------|--------|
| 151 | Fork V2 + strip divergence + reduce to 2 symbols | completed |
| 152 | Rewrite request.security() calls (15→8) | completed |
| 153 | Add 52 position state var declarations + clearing logic | completed |
| 154 | Add staleness + setup detection + exit detection logic | completed |
| 155 | Rewrite compact JSON builders + alert generation | completed |
| 156 | Update combo_settings.yaml for V2 | completed |
| 157 | Add category-aware symbol pairing in tte/main.py | completed |
| 158 | Create branch, update docs, and open PR | completed |

### V2 Testing & Deployment (Pending)

| # | Task | Status | Blocked By |
|---|------|--------|------------|
| 159 | Validate config with new V2 settings (`--validate`) | pending | — |
| 160 | Upload V2 indicator to TradingView + verify compilation | pending | — |
| 161 | Test setup conditions, signals, and exits in indicator | pending | #160 |
| 162 | Rebuild TTE.exe with V2 changes | pending | — |
| 163 | Create alerts with `--fresh` using V2 indicator | pending | #159, #160, #162 |
| 164 | Test webhook delivery with V2 compact payload | pending | #163 |

---

## Session History

### Session: 2026-02-26 (V2 Implementation — Pine Script + Python + PR)

**Goal**: Execute the V2 implementation plan — build Pine Script V2, update Python, open PR.

**What was built**:

#### Pine Script V2 (`Pine Script Code/TTE Screener V2.txt`)
Forked from V1 screener (1267 lines). Major changes:
- **Indicator declaration**: `TTE Screener V2`, `max_bars_back=5000` for 30s chart history
- **Reduced to 2 symbols**: Deleted s03-s20 inputs, `usedSymbols` default = 2
- **Removed divergence**: Deleted ~220 lines (calcKernelOsc, swing point detection, bullish/bearish div functions), removed KernelFunctions library import
- **checkSignalWithOB()**: Returns 20 values (was 24 — removed 4 divergence return values)
- **8 request.security() calls** (was 15): 2×1H, 2×H4 (NWE+OB), 2×D1 (OB only), 2×chartTF (close+high+low+time via tuple return)
- **52 `var` position state variables**: 13 per position × 4 positions (s1 buy/sell, s2 buy/sell). Fields: entry, sl, tp, entryTime, label, nweTf, obTf, isNew, exited, exitType, exitPrice, exitTime, exitSent
- **Clearing logic**: exitSent positions cleared at bar start, isNew reset after first bar
- **Staleness**: `timenow - symTime > 120000` excludes closed-market symbols
- **Setup detection**: LTF (1H NWE + H4/D1 OB) checked before HTF (H4 NWE + D1 OB). SL = MIN/MAX of confirming OB zones. TP = 1:2 RR. Validates SL on correct side of entry.
- **Exit detection**: Candle high/low vs TP/SL. TP checked before SL.
- **Compact JSON builders**: `abbreviateZone()`, `abbreviateSubtype()`, `buildNweV2()`, `buildObV2()`, `buildPosV2()`, `buildSymV2()` — all using abbreviated keys
- **Alert**: `alert.freq_once_per_bar_close`, payload = `{"ts":...,"s":[...]}`
- **exitSent flag**: Set AFTER alert fires so exit data is sent once before position clears
- **V2 debug table**: 2 symbols, no DIV columns, added Buy/Sell/Stale columns

#### Python Changes
- **`tte/main.py`**: Replaced `fetch_all_symbols()` with `fetch_symbols_by_category(batch_size: int)` — batches symbols within same category. Call site updated to `batches, total = fetch_symbols_by_category(config.batch_size)`. `chunk_symbols()` kept for backward compat.
- **`combo_settings.yaml`**: 5 values changed: `chart_timeframe: "30 seconds"`, `screener.shorttitle: "Screener V2"`, `screener.name: "TTE Screener V2"`, `alerts.batch_size: 2`, `maintenance.interval: 150`

#### Docs & PR
- **`docs/combo/ARCHITECTURE.md`**: Added V2 section at top (what changed table, V2 indicator details, category pairing, compact payload format, position lifecycle, V2 files)
- **`CLAUDE.md`**: Updated Combo Mode description and settings table for V2 defaults
- **Branch**: `feat/screener-v2`, **PR #8**: https://github.com/Samaara-Das/Tradingview-to-Everywhere/pull/8
- **Commit**: `4f7d0ab` — all pre-commit hooks passed (ruff, pyright)

#### Bugs Fixed During Implementation
1. **Divergence deletion incomplete**: First edit only replaced the header, leaving ~220 lines of function bodies. Required second large edit.
2. **`config.batch_size` scoping bug**: Background agent created `fetch_symbols_by_category()` referencing `config.batch_size`, but `config` is local to `main()`. Fixed by adding `batch_size: int` parameter.
3. **OB subtype abbreviation**: Plan used `"ef"` for bearish FVG but agent-comms spec used `"brf"`. Standardized to `"brf"`.

---

### Session: 2026-02-26 (V2 Architecture Shift — Planning + MongoDB)

**Goal**: Plan and begin implementing a major architecture shift for TTE.

**What changed**:
- **Scale**: ~1028 symbols / ~343 alerts → 626 symbols / ~314 alerts (2 per alert)
- **Chart**: 1-minute → 30-second with `alert.freq_once_per_bar_close`
- **Setup tracking**: Moved from Stock Buddy into Pine Script
- **Exit tracking**: Moved from planned Stock Buddy cron into Pine Script
- **Divergence**: Removed entirely
- **Payload format**: Raw signals → signals + setups + exits (compact JSON)

- Plan file created at `.claude/plans/reflective-petting-flame.md`
- Agent comms rewritten for Stock Buddy (`.claude/agent-comms.md`)
- MongoDB symbols updated: 1028 → 626 (376 US, 201 Indian, 29 Forex, 20 Crypto)

---

### Previous Sessions (Summary)
- **2026-02-23**: Snapshot quality + GUI defaults (PR #7 → `d8cd061`)
- **2026-02-21**: Snapshot reliability — `_wait_for_indicator_ready()`, backfill endpoint
- **2026-02-20**: Chart snapshots feature (PR #6), Trade Drawer v6, dual-timer maintenance
- **2026-02-13**: Codebase reorganization into `tte/` package (PR #4)
- **2026-02-12**: Pine Script screener, entry setups, divergence fix, GUI stop button
- **2026-02-10–11**: Single browser optimization, maintenance loop, Stock Buddy combo API

---

## Important Decisions Made

### V2 Architecture Decisions (2026-02-26)
1. **Indicator over Strategy**: `strategy.entry/exit` only works for chart symbol, not `request.security()` symbols.
2. **30-second chart**: `alert.freq_once_per_bar_close` — fires every 30s when data exists.
3. **Setup/exit in Pine Script**: All tracking in Pine `var` state. No Stock Buddy cron needed.
4. **Remove divergence**: Deleted ~220 lines in Pine Script, removed from payload.
5. **Compact JSON keys**: Abbreviated keys for TradingView's ~2KB alert message limit.
6. **Category-aware pairing**: Symbols paired within same asset class for matching market hours.
7. **Staleness detection**: `timenow - symTime > 120000` — stale symbols excluded.
8. **Position lifecycle**: `null → {n:true} → {n:false} → {xt:"tp"} → null`.
9. **HAL collision**: NSE:HAL for Indian, HAL for US.
10. **Max 1 buy + 1 sell per symbol**: First-to-trigger wins, LTF before HTF.
11. **SL**: MIN(confirming OB zoneLow) for buys, MAX(zoneHigh) for sells.
12. **TP**: 1:2 risk-reward → `entry ± 2 × |entry - sl|`.
13. **Stock Buddy hard swap**: Same `/api/tte/combo` endpoint, wipe old collections, `{symbol}-{direction}` dedup.

### Previous Decisions (2026-02-20–23)
14. **Snapshot architecture**: Async polling (TTE polls Stock Buddy every 60s).
15. **Alt+S for snapshots**: Clipboard via `navigator.clipboard.readText()` + CDP headless permission.
16. **Pre-commit hooks**: ruff (lint + format) + pyright (type check).
17. **Webhook URL in YAML**: Production URL kept in `combo_settings.yaml`.

---

## Key Reference Files

### TTE Project
| File | Purpose |
|------|---------|
| `Pine Script Code/TTE Screener V2.txt` | **V2 screener** with setup/exit tracking |
| `Pine Script Code/TTE Screener.txt` | V1 screener (archived, no longer in use) |
| `.claude/plans/reflective-petting-flame.md` | Full V2 architecture plan/PRD |
| `.claude/agent-comms.md` | Stock Buddy agent coordination (V2 payload spec) |
| `tte/main.py` | Entry point — `fetch_symbols_by_category()` for category pairing |
| `tte/config.py` | Config dataclass |
| `combo_settings.yaml` | Settings (30s, batch_size=2, 150s maintenance) |
| `tte/data/symbols.py` | MongoDB symbol fetching |
| `tte/browser/tradingview.py` | Browser automation |
| `tte/snapshot_worker.py` | Snapshot polling (unchanged) |
| `tte_gui.py` | GUI (reads YAML dynamically) |

### Stock Buddy App
| File | Purpose |
|------|---------|
| `src/app/api/tte/combo/route.ts` | Combo webhook handler (needs V2 update — Stock Buddy scope) |
| `src/app/api/tte/snapshots/*/route.ts` | Snapshot API endpoints (unchanged) |

---

## V2 Compact Payload Format

```json
{
  "ts": 1707264000000,
  "s": [{
    "sym": "GBPAUD", "c": 1.985,
    "nwe": [{"z": "la", "t": "bull", "tf": "1H", "ots": 1707264000}],
    "ob": [{"zt": "OB", "st": "un", "t": "bull", "zh": 1.99, "zl": 1.97, "tf": "H4", "zts": 1707260400, "ots": 1707264000}],
    "b": [{"e": 1.98, "sl": 1.975, "tp": 1.99, "et": 1707260000, "l": "LTF", "ntf": "1H", "otf": "H4", "n": true}, null],
    "se": [null, null]
  }]
}
```

**Key legend**: `ts`=timestamp, `s`=symbols, `sym`=symbol, `c`=close, `nwe`=NWE signals, `ob`=OB/FVG signals, `b`=buy positions [LTF, HTF], `se`=sell positions [LTF, HTF], `e`=entry, `sl`=stopLoss, `tp`=takeProfit, `et`=entryTime, `l`=label(LTF/HTF), `ntf`=nweTf, `otf`=obTf, `n`=isNew, `xt`=exitType(tp/sl), `xp`=exitPrice, `xts`=exitTime

---

## Verified Patterns

### Snapshot API Contract (unchanged)
```
GET  /api/tte/snapshots/pending?limit=5
POST /api/tte/snapshots/update  (success: {setupMessageId, snapshotUrl, snapshotTvUrl})
POST /api/tte/snapshots/backfill
```

### Working TradingView Selectors
```
Legend items:      div[data-qa-id="legend-source-item"]  (data-status="loading" while loading)
Legend toggler:    button[data-qa-id="legend-toggler"]
Indicator inputs:  input[data-qa-id="ui-lib-Input-input"]
Indicator title:   JS: querySelectorAll('div[class*="title-"]')[0].textContent
Settings dialog:   div[data-name="indicator-properties-dialog"]
Inputs tab:        button[id="inputs"]
Submit button:     button[name="submit"]
```

### MongoDB Symbols Schema
```json
{ "symbol": "NVDA", "full_symbol": "NVDA", "category": "US Stocks" }
```
Categories: `Currencies`, `Crypto`, `US Stocks`, `Indian Stocks`
Unique index on `symbol` field.

---

## Test Commands

```bash
# TTE
python combo_main.py --maintain-only    # Run maintenance + snapshots (headless)
python combo_main.py --validate         # Validate config
python combo_main.py --fresh            # Delete alerts & recreate
dist/TTE.exe                            # GUI (requires pystray)

# MongoDB symbol counts
pipenv run python -c "
import pymongo, os; from dotenv import load_dotenv; load_dotenv('.env')
from collections import Counter
col = pymongo.MongoClient(os.getenv('MONGODB_URI'))['tte']['symbols']
cats = Counter(doc['category'] for doc in col.find({}, {'category': 1}))
for cat, count in sorted(cats.items()): print(f'{cat}: {count}')
print(f'Total: {sum(cats.values())}')
"
```
