# Task Context Tracker

**Last Updated**: 2026-02-27
**Current Task**: V2 fully operational + all docs updated. Only pending task: #147 (testing strategy).
**Active Branch**: `main`
**Latest Commit (TTE)**: `4bacff0` — Docs: update all documentation for V2 architecture (#9)
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
| 153 | Add position state var declarations + clearing logic | completed |
| 154 | Add staleness + setup detection + exit detection logic | completed |
| 155 | Rewrite compact JSON builders + alert generation | completed |
| 156 | Update combo_settings.yaml for V2 | completed |
| 157 | Add category-aware symbol pairing in tte/main.py | completed |
| 158 | Create branch, update docs, and open PR | completed |

### V2 Testing & Deployment

| # | Task | Status | Blocked By |
|---|------|--------|------------|
| 159 | Validate config with new V2 settings (`--validate`) | completed | — |
| 160 | Upload V2 indicator to TradingView + verify compilation | completed (needs re-upload after LTF/HTF refactor) | — |
| 161 | Test setup conditions, signals, and exits in indicator | completed (verified via code comparison) | — |
| 162 | Rebuild TTE.exe with V2 changes | completed (11.3MB) | — |
| 163 | Create alerts with `--fresh` using V2 indicator | completed | — |
| 164 | Test webhook delivery with V2 compact payload | completed | #163 |

---

## Session History

### Session: 2026-02-27 (Docs Update + Git Cleanup)

**Goal**: Update docs-updater agent for TTE, run comprehensive docs audit, clean up stale git branches, merge docs to main.

**What was done**:
1. **Rewrote `.claude/agents/docs-updater.md`**: Was copied from Stock Buddy — rewritten for TTE with correct doc tiers, file paths, codebase areas, and workflow
2. **Updated `.claude/skills/update-docs/references/doc-inventory.md`**: Rewritten for TTE documentation structure
3. **Ran docs-updater agent**: Comprehensive audit updated 10 files — CLAUDE.md, ARCHITECTURE.md, PRD.md, API.md, DATABASE.md, SETUP.md, README.md, doc-inventory. All V1 sections updated to V2 values.
4. **Fixed CLAUDE.md**: Webhook interval 30s→45s (matches actual `combo_settings.yaml`)
5. **Deleted 7 stale remote branches**: `combo-architecture`, `multi-alert`, `point-capital`, `single-alert`, `tiered-orchestrator`, `feat/screener-v2`, `feat/snapshot-quality-gui-defaults`, `feature/chart-snapshots` — all from merged/closed PRs
6. **PR #9 created and merged**: `4bacff0` — Docs: update all documentation for V2 architecture
7. **Updated MEMORY.md**: Fixed rate limiting section for V2, added V2 architecture summary

**Note**: Chart timeframe is **45 seconds** (not 30s as previously documented). Verified against `combo_settings.yaml`.

---

### Session: 2026-02-26 (Stale CSS Selectors Fix + V2 Webhook Confirmed)

**Goal**: Fix `--fresh` failing to detect/delete existing alerts, and confirm V2 webhook delivery end-to-end.

**Root cause**: TradingView changed dynamically generated CSS class names (e.g., `itemBody-ucBqatk5` → new hash). Three hardcoded selectors in `tte/browser/tradingview.py` matched nothing, so `delete_all_alerts()` and `no_alerts()` always thought there were no alerts. Old V1 alerts kept firing, Stock Buddy rejected them with 400 Bad Request (V2-only now).

**Changes made** (`tte/browser/tradingview.py`):

1. **Alert existence check** (line 1068): `"div.list-G90Hl2iS div.itemBody-ucBqatk5"` → `'div[data-name="alert-item-name"]'` — stable `data-name` attribute
2. **Debug logging** (lines 1073-1077): Added `find_elements('[data-name^="alert-"]')` debug log before "no alerts" message
3. **Dropdown option selector** (line 1048): `"div.item-jFqVJoPk"` → `'div[data-qa-id="menu-inner"] > div'` — stable `data-qa-id` container
4. **`no_alerts()` rewrite** (lines 1312-1332): Replaced stale class selector + fixed logic bug where `TimeoutException` (= no alerts found) fell into generic `except` returning `False` instead of `True`. Now has separate `except TimeoutException: return True` branch.

**EXE rebuilt**: 12MB, all validation passed. Committed as `77d081c`.

**Webhook delivery confirmed**: User tested and confirmed V2 webhooks are being sent and received by Stock Buddy.

**Symbols investigation**: Both TTE and Stock Buddy read from the **same** MongoDB `symbols` collection (database `tte`, cluster `cluster1.565lfln.mongodb.net`). 626 symbols currently (Currencies: 29, Crypto: 20, US Stocks: 376, Indian Stocks: 201). No seed script exists — collection was populated externally. Header comment in `symbols.py` is stale (says 1054).

**Next steps**: User will test Stock Buddy V2 adaptation and run TTE EXE for alert creation + maintenance.

---

### Session: 2026-02-26 (Graceful Shutdown for TTE)

**Goal**: Make Ctrl+C shutdown complete in ~2-3 seconds with clean log output instead of ~30 seconds with noisy connection-refused errors.

**Root cause of slow shutdown**:
1. On Windows, Ctrl+C propagates to entire process group — Chrome/ChromeDriver die immediately, making WebDriver socket dead
2. Operations continue after `_shutdown_requested` is set — `change_layout()`, snapshot worker init, etc. still run and hit 10s WebDriverWait timeouts against dead browser
3. `driver.quit()` on dead browser takes ~16s — urllib3 retries dead connection multiple times

**Changes made** (`tte/main.py`):

1. **`threading.Event` replaces boolean flag**: `_shutdown_requested = False` → `_shutdown_event = threading.Event()`. Enables interruptible waits via `.wait(timeout)`.
2. **All `sleep()` → `_shutdown_event.wait()`**: Returns instantly when shutdown signaled. Applies to: recalc waits, alert creation delay, maintenance tick loop, post-refresh wait, post-restart/clear-log waits.
3. **`_force_close_browser()` helper**: Tries `driver.quit()` first; if it hangs (dead browser), force-kills ChromeDriver process tree via `taskkill /F /T` (Windows) or `os.kill(SIGKILL)` (Unix).
4. **Shutdown checks before every browser operation**: Before `change_layout()`, snapshot worker init, each maintenance cycle, after refresh wait, before `save_layout()`, before entering maintenance.
5. **Early return in `restart_inactive_alerts()` / `clear_alert_log()`**: Check `_shutdown_event.is_set()` at entry.
6. **Suppressed noisy errors during shutdown**: Exception handlers log at `DEBUG` instead of `ERROR`/`EXCEPTION` when shutdown is active.
7. **Removed unused imports**: `sleep`, `contextlib` removed; added `os`, `platform`, `subprocess`, `threading`.

**EXE rebuild**: Triggered after code changes.

---

### Session: 2026-02-26 (Bug Fix: delete_all_alerts race condition)

**Goal**: Fix `delete_all_alerts()` failing to detect existing alerts when running `--fresh`.

**Root cause**: `find_elements()` at `tradingview.py:1065` was instant (no wait). If the alert list DOM hadn't finished rendering after opening the sidebar, it returned `[]` and the method exited thinking there were no alerts.

**Fix applied** (`tte/browser/tradingview.py:1064-1071`):
- Replaced instant `find_elements()` with `WebDriverWait(driver, 3).until(EC.presence_of_element_located(...))`
- Polls up to 3 seconds for alert elements. Only reports "no alerts" if nothing renders within that window.
- Config validation passed (`--validate`). EXE rebuild triggered.

---

### Session: 2026-02-26 (LTF/HTF Independent Positions Refactor)

**Goal**: Continue from previous session — complete the LTF/HTF refactor so both setup types coexist independently.

**Context**: User requested "if an HTF and LTF setup exist, both should be sent in the payload and not just the LTF/HTF one". Previous session had completed var declarations, clearing, isNew reset, setup detection, and exit detection. JSON builders/payload/exitSent still needed updating.

**What was done (this session)**:

1. **Updated `buildPosV2()`**: Replaced `label` param with `ltfOrHtf` string ("LTF"/"HTF") — label field now encoded in slot name
2. **Updated `buildSymV2()`**: Changed signature to accept 4 position strings (buyLtf, buyHtf, sellLtf, sellHtf). Payload format changed from `"b":{single}` to `"b":[ltfPos,htfPos]`
3. **Updated position JSON build calls**: 8 `buildPosV2()` calls instead of 4 (buy01_ltf, buy01_htf, sell01_ltf, sell01_htf, etc.)
4. **Updated `buildSymV2()` calls**: Now pass 4 position strings per symbol
5. **Updated exitSent flags**: 8 blocks instead of 4
6. **Updated debug table**: 12 columns (added BuyLTF, BuyHTF, SellLTF, SellHTF), all using new `pos_s1bl_*` etc. var names. Commented out for production.
7. **Verified no old var name references remain** (`pos_s1b_`, `pos_s1s_`, `pos_s2b_`, `pos_s2s_` — all gone)
8. **Updated docs**:
   - `agent-comms.md`: Payload examples with arrays, dedup key changed to `{symbol}-{direction}-{label}`, lifecycle examples updated
   - `ARCHITECTURE.md`: Position tracking (96 vars, 8 positions), payload format, lifecycle
   - `task-context.md`: Payload format
9. **Pine Script expert review**: All checks passed (v6 syntax, barstate.isconfirmed, var usage, JSON validity, no repainting, 8 request.security calls). Payload size ~2KB worst case.
10. **Committed**: `9824be9` — Independent LTF/HTF positions: 8 slots, array payload format
11. **Added 15 dummy symbol inputs** (`d01`–`d15`): Extend settings panel for Selenium scrolling
12. **Committed**: `211e72c` — Add 15 dummy symbol inputs to extend settings panel for Selenium
13. **User confirmed**: Screener V2 is favorited in TradingView. No EXE rebuild needed (only Pine Script changed).

**Bugs Fixed**: None this session (clean refactor).

**Key clarifications**:
- **4 setups per symbol max**: 1 LTF buy + 1 HTF buy + 1 LTF sell + 1 HTF sell
- **No cross-restrictions**: LTF buy doesn't block HTF buy or any sell. Each slot independent.
- **EXE rebuild not needed**: Python code unchanged since last build.

---

### Session: 2026-02-26 (V2 Testing, Compilation Fix, Code Verification)

**Goal**: Execute testing tasks #159–#162, verify V2 indicator correctness.

**What was done**:
- **Task #159**: `--validate` passed
- **Task #162**: TTE.exe rebuilt (11.3MB)
- **Task #160**: User uploaded indicator. Hit compilation error: `Could not find method 'rationalQuadratic' for 'kernels'`. Fixed by restoring `import jdehorty/KernelFunctions/2 as kernels` (was incorrectly removed — NWE's `calcNWE()` uses it, not just divergence).
- **Task #161**: Instead of manual testing, ran `diff` comparing V1 vs V2 for all core functions (calcNWE, scanOBRange, getNweZoneName, checkSignalWithOB). Result: ALL V1 calculations preserved exactly, only divergence removed. V2 new code (setups/exits) logically correct.
- **Debug table**: Uncommented with NWE/OB data cells + color coding, then re-commented for production.
- **User feedback**: "if an HTF and LTF setup exist, both should be sent" → triggered the LTF/HTF refactor (completed in next session above).

---

### Session: 2026-02-26 (V2 Implementation — Pine Script + Python + PR)

**Goal**: Execute the V2 implementation plan — build Pine Script V2, update Python, open PR.

**What was built**:
- Pine Script V2 forked from V1 (1267 lines), divergence removed, reduced to 2 symbols
- 8 `request.security()` calls, position state tracking, compact JSON builders
- Python: `fetch_symbols_by_category(batch_size)` in `tte/main.py`, `combo_settings.yaml` updated
- Docs updated, branch `feat/screener-v2` created, PR #8 opened
- Commit: `4f7d0ab`

**Bugs fixed**: Divergence deletion incomplete, `config.batch_size` scoping bug, OB subtype abbreviation mismatch.

---

### Session: 2026-02-26 (V2 Architecture Shift — Planning + MongoDB)

**Goal**: Plan major architecture shift. Scale: ~1028→626 symbols, 1min→45s chart, setup/exit tracking moved to Pine Script, divergence removed.
- Plan file: `.claude/plans/reflective-petting-flame.md`
- Agent comms rewritten: `.claude/agent-comms.md`
- MongoDB symbols updated: 1028 → 626

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
2. **45-second chart**: `alert.freq_once_per_bar_close` — fires every 45s when data exists.
3. **Setup/exit in Pine Script**: All tracking in Pine `var` state. No Stock Buddy cron needed.
4. **Remove divergence**: Deleted ~220 lines in Pine Script, removed from payload.
5. **Compact JSON keys**: Abbreviated keys for TradingView's ~2KB alert message limit.
6. **Category-aware pairing**: Symbols paired within same asset class for matching market hours.
7. **Staleness detection**: `timenow - symTime > 120000` — stale symbols excluded.
8. **Position lifecycle**: `null → [ltf,htf] → exit → null` per slot.
9. **Independent LTF/HTF**: 4 positions per symbol max (LTF buy, HTF buy, LTF sell, HTF sell). No cross-restrictions.
10. **SL**: MIN(confirming OB zoneLow) for buys, MAX(zoneHigh) for sells.
11. **TP**: 1:2 risk-reward → `entry ± 2 × |entry - sl|`.
12. **Stock Buddy hard swap**: Same `/api/tte/combo` endpoint, wipe old collections, `{symbol}-{direction}-{label}` dedup.
13. **Array payload**: `"b":[ltfPos, htfPos]`, `"se":[ltfPos, htfPos]` — both slots always present.

### Graceful Shutdown (2026-02-26)
18. **`threading.Event` over boolean**: Enables `_shutdown_event.wait(N)` which returns instantly on signal vs `sleep(N)` + polling.
19. **Force-kill over graceful quit**: On Ctrl+C, Chrome is already dead; `driver.quit()` hangs 16s on urllib3 retries. `taskkill /F /T /PID` is instant.
20. **DEBUG logging during shutdown**: Prevents noisy `ConnectionRefusedError` / `MaxRetryError` tracebacks that alarm users.

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
| `Pine Script Code/TTE Screener V2.txt` | **V2 screener** with independent LTF/HTF setup/exit tracking |
| `Pine Script Code/TTE Screener.txt` | V1 screener (archived, no longer in use) |
| `.claude/plans/reflective-petting-flame.md` | Full V2 architecture plan/PRD |
| `.claude/agent-comms.md` | Stock Buddy agent coordination (V2 array payload spec) |
| `tte/main.py` | Entry point — `fetch_symbols_by_category()` for category pairing |
| `tte/config.py` | Config dataclass |
| `combo_settings.yaml` | Settings (45s, batch_size=2, 150s maintenance) |
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
Alert items:       div[data-name="alert-item-name"]              (stable — use instead of class-based selectors!)
Alert settings:    div[data-name="alerts-settings-button"]
Dropdown menu:     div[data-qa-id="menu-inner"] > div            (children = Stop All, Delete All Inactive, etc.)
```

**WARNING**: Never use TradingView's dynamically generated class names (e.g., `itemBody-ucBqatk5`, `item-jFqVJoPk`, `list-G90Hl2iS`). These change between UI builds. Always prefer `data-name` and `data-qa-id` attribute selectors.

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
pipenv run python combo_main.py --maintain-only    # Run maintenance + snapshots (headless)
pipenv run python combo_main.py --validate         # Validate config
pipenv run python combo_main.py --fresh            # Delete alerts & recreate
dist/TTE.exe                                       # GUI (requires pystray)

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
