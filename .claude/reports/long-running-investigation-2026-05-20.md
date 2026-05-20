# Long-Running Setups Investigation — 2026-05-20

## TL;DR

- **Pine V2 is stateless** — it does NOT emit exit signals and has NO expire/max-age clause. Setups can theoretically run forever from Pine's side. All exit detection is Stock Buddy's `/api/cron/check-exits` job (per `CLAUDE.md` "V2 Architecture" and `Pine Script Code/TTE Screener V2.txt` lines 9, 504).
- Of the **24 long-running (>40 days) setups**, daily-candle inspection against Yahoo Finance shows:
  - **23 are legitimately running** — neither raw TP nor raw SL was touched at the daily resolution since `entryTime`.
  - **1 setup (MAHLIFE) shows a raw SL cross on 2026-04-08** the day after entry, which SB's exit cron appears to have missed. This is an SB-side question, not a TTE Pine question.
- **No Pine fix needed.** If the product wants stale setups to auto-resolve, that's a Nili decision and an SB-cron change (add max-age `outcome:"expired"` rule).

## Investigation method

1. Queried `tte.setup_messages` on the prod Atlas (`stock-buddy.8kc2y6`) for all running setups; 24 had `ageDays >= 40` as of `2026-05-20`.
2. For each, fetched **daily candles** from Yahoo Finance since `entryTime - 1d` to today:
   - Currencies: `NZDUSD=X`
   - US stocks: ticker as-is
   - Indian stocks: `<TICKER>.NS` (NSE)
3. For each daily bar, checked the **raw direction** thresholds:
   - Raw Sell: `low ≤ raw_TP` (TP hit) or `high ≥ raw_SL` (SL hit)
   - Raw Buy: `high ≥ raw_TP` or `low ≤ raw_SL`
4. Raw script + raw JSON output: `scripts/investigate_stale.py`, `scripts/investigate_stale.json`.

> Caveat: Yahoo daily resolution can miss intraday wicks that an intra-hour exit-cron would catch. SB's cron uses Binance (crypto) / Yahoo (stocks) — same data source. For symbols already at the daily resolution, divergence between this audit and SB's cron should be minimal except at gap opens. The one cross I did find (MAHLIFE) was a clear daily-high gap, well within Yahoo's coverage.

## Pine-script "expire after N days"?

**No such clause exists.** `Pine Script Code/TTE Screener V2.txt`:

- Line 9 (header): *"Stock Buddy handles deduplication (partial unique DB index) and exit detection (server-side cron)."*
- Line 504: *"Build compact setup JSON — stateless, no exit fields. Stock Buddy handles dedup (partial unique index) and exit detection (cron)."*
- Only `alert()` call (line 690) emits the setup creation payload `{e, sl, tp, et, l, ntf, otf}` — no exit/expire emission anywhere.
- No `var` state, no time-based comparison against `entryTime`, no "close after N bars" logic.

Setups outlive TP/SL crossing only if SB's cron also misses them. From Pine's perspective, every fresh-bar evaluation creates a new setup if the alignment is still present; resolution is SB's job.

## Per-symbol verdict

Format: `symbol (direction)  entry → TP / SL  | ageDays | minLow_since_entry / maxHigh_since_entry | verdict`

Raw direction shown (the direction Pine emitted). SB display direction is the inverse.

### Setups with NO crossing on daily candles — legitimately running (23)

| Symbol | Dir | Entry | Raw TP | Raw SL | Age | minLow | maxHigh | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| NZDUSD | Sell | 0.59086 | 0.56718 | 0.6027 | 77d | 0.56877 | 0.59903 | running — Yahoo daily never reached SL (0.6027) nor wicked into TP (0.56718). minLow 0.56877 is **0.28%** above TP. |
| NDAQ | Sell | 89.15 | 74.55 | 96.45 | 76d | 81.00 | 93.63 | running — daily high stayed 2.92% below SL; daily low stayed 8.65% above TP. |
| MCO | Sell | 473.47 | 386.81 | 516.80 | 76d | 422.16 | 482.54 | running — wide SL never approached; low never crossed TP. |
| INDIGO | Sell | 4460 | 3580.20 | 4899.90 | 76d | 3895.20 | 4748.30 | running — but minLow 3895.2 is **8.79%** above TP; close to a TP hit, never crossed. |
| POWERGRID | Buy | 291.65 | 332.55 | 271.20 | 72d | 283.50 | 324.95 | running — maxHigh 324.95 is **2.29%** below TP; low never reached SL. |
| ATGL | Buy | 588.65 | 803.95 | 481.00 | 68d | 490.00 | 684.90 | running — both sides remain wide of TP/SL. |
| WAAREEENER | Buy | 3081.30 | 3607.90 | 2818.00 | 58d | 2961.30 | 3557.00 | running — maxHigh **1.41%** below TP. |
| THYROCARE | Buy | 348.00 | 708.87 | 167.57 | 58d | 342.55 | 526.00 | running — TP 708.87 is +103.7% above entry (extreme); SL 167.57 is -51.85% below. minLow 342.55 barely touched entry, never close to SL. **See subtask-B report for the underlying D1 FVG anchor (zoneLow=167.57, zoneHigh=455.55, FVG width = 287.99).** |
| CPRT | Sell | 33.765 | 31.755 | 34.77 | 58d | 32.24 | 34.52 | running — TP only 1.54% below minLow; maxHigh 0.72% below SL. Tight range. |
| CTAS | Sell | 179.71 | 158.49 | 190.32 | 56d | 161.16 | 186.05 | running — minLow 1.68% above TP; close call. |
| SUPRAJIT | Sell | 415.40 | 332.00 | 457.10 | 54d | 396.60 | 450.00 | running — both sides comfortably away. |
| TRIVENI | Buy | 381.60 | 438.90 | 352.95 | 51d | 362.85 | 435.00 | running — maxHigh 0.89% below TP. |
| PETRONET | Sell | 258.90 | 202.20 | 287.25 | 49d | 247.09 | 286.80 | running — maxHigh 0.16% below SL. Near miss. |
| AES | Sell | 14.30 | 9.1056 | 16.8972 | 47d | 14.07 | 14.61 | running — extremely tight: minLow 54.5% above TP. |
| HDFCBANK | Sell | 806.65 | 739.05 | 840.45 | 42d | 747.00 | 820.05 | running — minLow 1.07% above TP. |
| BAJAJFINSV | Sell | 1789.50 | 1618.90 | 1874.80 | 42d | 1625.00 | 1860.00 | running — minLow 0.38% above TP. |
| MUTHOOTFIN | Sell | 3482.10 | 3020.70 | 3712.80 | 42d | 3225.50 | 3678.50 | running. |
| AXON | Sell | 406.20 | 328.68 | 444.96 | 42d | 339.01 | 438.97 | running. |
| FER | Sell | 70.16 | 62.34 | 74.07 | 41d | 64.67 | 72.47 | running. |
| UPL | Sell | 640.95 | 504.65 | 709.10 | 41d | 615.00 | 682.60 | running. |
| AIG | Sell | 77.54 | 67.24 | 82.69 | 41d | 72.98 | 79.77 | running. |
| SCHW | Sell | 97.63 | 77.89 | 107.50 | 40d | 87.61 | 100.76 | running. |
| EICHERMOT | Sell | 7274.50 | 6675.50 | 7574.00 | 40d | 6752.50 | 7471.50 | running. |

### Setups where raw SL/TP did cross on daily candles (1)

| Symbol | Dir | Entry | Raw TP | Raw SL | Age | Cross detected |
|---|---|---:|---:|---:|---:|---|
| **MAHLIFE** | Sell | 330.35 | 283.85 | 353.60 | 43d | Yahoo daily `2026-04-08` high ≥ 353.60 (the day after entry on 2026-04-07). **Raw SL was crossed; setup should have resolved as `sl_hit` (raw) → `tp_hit` (display).** |

This is an SB-side question — Pine cannot know about exits. Either (i) SB's exit cron missed the cross, (ii) the data source SB uses (Binance/Yahoo via SB's own client) didn't record the same high, or (iii) the cross happened intraday but the cron's closed-candle policy filtered it out. **Recommend SB rerun `/api/cron/check-exits` against MAHLIFE and inspect.**

## Recommendations

1. **No Pine V2 change.** The "no exit emission, no expire clause" behaviour is the documented V2 architecture (CLAUDE.md). Adding a max-age expire to Pine would be a redesign and is out of scope.
2. **Product decision needed (Nili):** if stale running setups (>40d, >60d) should be auto-closed as `outcome:"expired"`, that's an **SB cron** rule, not a TTE Pine rule. Options:
   - Add max-age sweep to `/api/cron/check-exits` (e.g., after N days with no cross, mark `outcome:"expired"`).
   - Surface long-running setups in UI as a separate badge ("running 60d+") so users have context.
3. **Investigate MAHLIFE individually** — possible SB cron miss on the daily SL cross 2026-04-08. Hand off to SB.
4. **THYROCARE in particular** — the D1 FVG zone Pine anchored to (167.57 → 455.55) is enormous (287.99 INR / ~83% of entry width). This is a legitimate but extreme outlier; see subtask B for the formula trace.

## Questions for SB

- For MAHLIFE 2026-04-08: did `/api/cron/check-exits` see this bar? If yes, why did it not flip the outcome? If no, is the data source/window missing it?
- Is Nili open to a max-age expire rule on the SB side? If yes, what N (30d? 60d? 90d?) and what `outcome` value?

## Artefacts

- Script: `scripts/investigate_stale.py`
- Raw JSON: `scripts/investigate_stale.json`
- Pine source: `Pine Script Code/TTE Screener V2.txt` (lines 1-700)
- Audit input: `C:/Users/dassa/Work/Stock-Buddy-App/.claude/worktrees/feat-display-exit-97-post-pr600/.claude/reports/stale-setups-audit-2026-05-20.md`
