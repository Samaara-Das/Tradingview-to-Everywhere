# Snapshot pipeline root cause — 2026-05-14

## Diagnosis (AC6.2)

**Live tte-1 Chrome has been logged out of TradingView since 2026-05-08 15:13 UTC.**

Evidence (probe via DevTools port 33203, page target `https://www.tradingview.com/chart/yDNmRCDO/`):

- `document.title` = `"Chart Not Found — TradingView"`
- Body text starts: `"We can't open this chart layout for you. If you're the owner of this chart layout, then you need to log in to see it."`
- Every probed selector returns count=0:
  - `div.chart-markup-table` — 0 (this is why `_set_bars_to_right` throws NoSuchElementException at snapshot_worker.py:366)
  - `button#header-toolbar-symbol-search` — 0 (this is why `change_symbol` times out at chart.py:109)
  - `div[data-name="right-toolbar"] button[aria-label="Alerts"]` — 0 (this is why `open_alerts_sidebar` times out at tradingview.py:653)
  - `button[aria-controls="id_alert-widget-tabs-slots_tabpanel_log"]` — 0 (this is why `open_log_tab` fails at helpers.py:60)
- No overlay / dialog / toast / banner — the page is just the TV "Chart Not Found" placeholder

The Snapshot layout `yDNmRCDO` is an owner-only chart layout. When the session is logged out, TV serves the placeholder page instead of the chart. Every Selenium selector targeting chart components fails because **the chart simply doesn't exist on this page**.

The earlier hypothesis that "selectors broke after TV redesigned its UI" was wrong: all 6 selectors are intact in a logged-in chrome. The bug is **page state** (logged-out placeholder), not selector breakage.

## Why this happened

The tte-1 Chrome has been running for 6+ days under the same `--user-data-dir`. TV sessions expire (or get invalidated server-side); the long-lived Selenium-controlled Chrome had no re-login defense. On 2026-05-08 15:13 UTC the session became invalid; from that moment on every snapshot has failed.

## Fix plan (AC6.3)

**Three code changes + one immediate ops action**:

1. **`tte/browser/tradingview.py`** — add `is_chart_layout_loaded(driver) -> bool`:
   ```python
   def is_chart_layout_loaded(driver) -> bool:
       """Return True if the Snapshot/Screener layout is rendered (chart markup table present
       AND we're not on TV's 'Chart Not Found' / log-in placeholder page)."""
       title = (driver.title or '').lower()
       if 'chart not found' in title:
           return False
       try:
           driver.find_element(By.CSS_SELECTOR, 'div.chart-markup-table')
           return True
       except NoSuchElementException:
           return False
   ```

2. **`tte/snapshot_worker.py`** — at the top of each polling round (around the existing `_set_bars_to_right` call site), guard with re-login:
   ```python
   if not is_chart_layout_loaded(driver):
       log.error("Chart layout not loaded — TV session likely logged out. Attempting re-login.")
       sign_in_to_tradingview(driver)  # already exists in tradingview.py
       if not is_chart_layout_loaded(driver):
           log.error("Re-login failed — POSTing alert and skipping round.")
           _post_logged_out_alert()  # new helper, POST to 127.0.0.1:8765/alert
           return  # skip the round; next round will retry
   ```

3. **`tte/main.py::restart_inactive_alerts`** (maintenance) — same guard before any maintenance work.

4. **Immediate ops** (covered by #13 deploy): `docker stop tte-1 && docker compose up -d tte-1`. The startup orchestrator's existing sign-in path will re-establish the session. After deploy, snapshots resume.

## Code lines to patch

| File | Symbol | What |
|------|--------|------|
| `tte/browser/tradingview.py` | new `is_chart_layout_loaded()` | Detection helper |
| `tte/browser/tradingview.py` | maybe rename / re-export existing sign_in | Confirm symbol callable from snapshot_worker |
| `tte/snapshot_worker.py:~start of poll loop` | poll() / process_round() | Add login-state guard + re-login |
| `tte/main.py::restart_inactive_alerts` | maintenance entry | Same guard |
| New helper: cc-trigger alert poster | new in tradingview.py or new module | POST to local cc-trigger |

## Acceptance Criteria mapped to evidence

- AC6.1 ✓ — screenshot saved at `C:/Users/dassa/AppData/Local/Temp/tte1_state.png` (and on KVM8 at `/tmp/tte1_state.png`).
- AC6.2 ✓ — diagnosis above; observable difference is the TV "Chart Not Found" placeholder DOM (no chart, no toolbars, no indicators).
- AC6.3 ✓ — exact files + symbols + patch sketch listed above.
