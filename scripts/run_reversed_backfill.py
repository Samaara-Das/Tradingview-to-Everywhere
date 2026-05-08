"""Launcher for the reversed-strategy snapshot backfill.

Manager directive 2026-05-08 12:31 IST: backfill must run on a SEPARATE
TradingView profile (free TV account is fine for snapshot rendering) so
tte-1's `--maintain-only` instance stays untouched.

This launcher:
1. Forces `REVERSED_STRATEGY_SNAPSHOTS=true` (so the swap path runs).
2. Forces `CHROME_PROFILE` and `headless` so we never reuse tte-1's user-data-dir.
3. Builds a `Browser` on the "Snapshot" layout.
4. Constructs a `SnapshotWorker` and hands it to
   `tte.backfill_reversed_snapshots.run(worker)`.

Usage (from a separate machine or container — NOT on tte-1):

    BACKFILL_CHROME_PROFILE=BackfillProfile \
    MONGODB_URI=... \
    STOCK_BUDDY_DATABASE=stock_buddy_app \
    pipenv run python scripts/run_reversed_backfill.py

Status: STAGED. Do not run until:
- PR #32 has merged.
- Sammy has confirmed her Pine Script update does NOT also flip TP/SL
  (otherwise `REVERSED_STRATEGY_SNAPSHOTS` must be `false` here too).
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    # Force the reversal swap on at the env layer, before tte.config is imported.
    os.environ.setdefault("REVERSED_STRATEGY_SNAPSHOTS", "true")

    backfill_profile = os.getenv("BACKFILL_CHROME_PROFILE")
    if not backfill_profile:
        sys.stderr.write(
            "BACKFILL_CHROME_PROFILE is required. Use a profile name that is "
            "NOT the live tte-1 profile (e.g. 'BackfillProfile'). "
            "Aborting.\n"
        )
        return 2
    os.environ["CHROME_PROFILE"] = backfill_profile

    if not os.getenv("MONGODB_URI"):
        sys.stderr.write("MONGODB_URI is required (shared Atlas SRV string). Aborting.\n")
        return 2

    # Imports deferred so the env mutations above take effect.
    from tte import backfill_reversed_snapshots, log
    from tte.browser.tradingview import Browser
    from tte.config import ComboConfig
    from tte.snapshot_worker import SnapshotWorker, StockBuddyClient

    logger = log.setup_logger(__name__, log.INFO)
    config = ComboConfig()
    if not config.reversed_strategy_snapshots:
        logger.error(
            "config.reversed_strategy_snapshots is False — the launcher's env "
            "default did not take effect. Refusing to run a NON-reversed "
            "backfill (would overwrite snapshots with original-strategy visual)."
        )
        return 3

    logger.info(
        f"Reversed backfill starting on profile={backfill_profile!r} "
        f"layout={config.snapshot_layout_name!r}"
    )

    browser = Browser(
        keep_open=True,
        screener_shorttitle=config.screener_shorttitle,
        screener_name=config.screener_name,
        drawer_shorttitle="",
        drawer_name="",
        interval_minutes=config.maintenance_interval // 60,
        start_fresh=False,
        screener_ob_short=config.screener_shorttitle,
        screener_ob_name=config.screener_name,
        screener_nw_short=config.screener_shorttitle,
        screener_nw_name=config.screener_name,
        screener_sb_short=config.screener_shorttitle,
        screener_sb_name=config.screener_name,
        mode="combo",
        layout_name=config.snapshot_layout_name,
        chart_timeframe="1 hour",
        bar_style=config.snapshot_bar_style,
        headless=config.headless,
    )

    client = StockBuddyClient(config)
    worker = SnapshotWorker(browser=browser, config=config, client=client)

    try:
        backfill_reversed_snapshots.run(worker)
    except KeyboardInterrupt:
        logger.warning("Interrupted — checkpoint saved; rerun to resume.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
