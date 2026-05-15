# TTE Live Run — Monitoring Criteria

**Run timestamp**: 2026-05-05 ~14:36 IST
**Code version**: PR #28 merged (`7e5cf20`), local main being synced now
**Why python entry, not dist/TTE.exe**: The bundled exe was built before the PR #28 fix (snapshot at `~/TTE.exe.backup-20260504-173917`). Running `python -m tte.main` exercises identical code paths *with* the new `WebDriverWait(self.driver, 15)` fix. Rebuilding the PyInstaller bundle just to test is wasteful when the only difference is one line in `tte/browser/tradingview.py`.

## Run shape
- Command: `python combo_main.py --setup-only --symbols EURUSD,GBPUSD,BTCUSDT,ETHUSDT,RELIANCE`
- 5 symbols across 3 categories → 3 alerts (currencies pair, crypto pair, India singleton). Exercises symbol-pairing + `change_settings()` + alert dialog.
- Mode `--setup-only` exits after alert creation. If clean and time remains, follow up with a brief `--maintain-only` window.

## PASS criteria (all must hold)

### A. Process lifecycle
- A1. Process starts without import / config errors.
- A2. `python combo_main.py --validate` exits 0.
- A3. Process exits 0 at end of `--setup-only` run.

### B. Browser automation
- B1. Chrome launches successfully (headless per `combo_settings.yaml`).
- B2. TradingView login succeeds OR existing session resumes (no "Failed to sign in").
- B3. "Screener" layout opens.
- B4. Screener V2 indicator detected on chart (no `Could not find screener indicator` error).
- B5. **`change_settings()` succeeds at least once** — the legend-settings-action button click resolves within the 15s wait and the indicator-properties-dialog appears. This is the smoking-gun for PR #28's fix.
- B6. No `TimeoutException` raised in change_settings() flow.
- B7. No unhandled `StaleElementReferenceException`.

### C. Alert creation
- C1. At least one webhook alert created (`create_webhook_alert` returns success).
- C2. No "alert dialog stuck open" / "operator-dropdown not selectable" failures (PR #16-era bug, fixed but worth watching).
- C3. The condition dropdown shows "Any alert() function call" (verified post-create).
- C4. No alert-quota errors from TradingView.

### D. Data path
- D1. MongoDB symbols query succeeds (loads ≥5 symbols across categories).
- D2. Webhook URL is set and points at `stockbuddy.co/api/tte/combo`.

### E. Logs / observability
- E1. `app_log.log` is written (or `${LOG_DIR}/app_log.log`).
- E2. No Python `Traceback` lines.
- E3. No repeated retry-loop hammering (e.g. > 3 consecutive `Overlay blocking screener click` warnings without resolution).

## FAIL signatures (immediate diagnose-and-fix)

| Signature | Likely cause | Fix path |
|-----------|--------------|----------|
| `TimeoutException` on `legend-settings-action` | PR #28 fix didn't take | Verify branch is at `7e5cf20`, re-pull, re-run |
| `Failed to sign in to TradingView` | Stale TV session / 2FA / captcha | Check `.env` creds; if cookies stale, fall back to manual login window |
| `Could not find screener indicator: Screener V2` | Screener not on chart / wrong layout | Check `combo_settings.yaml` `layout_name` + `screener.shorttitle` |
| `MONGODB_PWD is required` / Mongo connection refused | `.env` missing | Inspect / create `.env` |
| `COMBO_WEBHOOK_URL is required` | env not loaded | Check `.env` and `tte/config.py` defaults |
| Chrome `--user-data-dir` lock error | another Chrome instance | Kill orphan Chrome processes |
| Pyright / ruff failure on launch | shouldn't happen at runtime — investigate |

## Stop conditions
- All A-E criteria green for ≥10 min of clean operation → declare PASS.
- Three consecutive failed run attempts on the same root cause → escalate to user.
- 25 min wall-clock cap on the whole exercise.
