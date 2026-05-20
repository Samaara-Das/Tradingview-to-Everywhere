# Wide SL/TP Placement Investigation — 2026-05-20

## TL;DR

- **The Pine SL formula is not buggy. It anchors SL to the matched OB/FVG zone edge — and that's what's wide.**
- **Pine TP is fixed at exactly `2 × (entry − SL)`** away from entry. So whenever SL is wide, TP is automatically twice as wide. There is no symbol-by-symbol asymmetry, no ATR-multiplier mistake, no swing-point miscount.
- Verdict per the brief: **(b) Correct Pine output; the underlying OB/FVG inputs are unusually wide for these specific symbols.** With a strong (c) flavour — the 2× TP relationship is intentional design (`Pine Script Code/TTE Screener V2.txt` lines 522, 531, 539, 548).
- Live values for NZDUSD / MCO / THYROCARE match the Pine formula exactly when re-derived from each setup's `signalSnapshot.ob_fvg` payload. **Not (a).**

## The formula (annotated)

From `Pine Script Code/TTE Screener V2.txt`:

### Setup branches (4 per symbol)

| Setup | Trigger | SL anchor | TP |
|---|---|---|---|
| LTF Buy  (line 517-524) | `nweBull_1h AND (bullF_h4 OR bullF_d1)` | `min(bullZL_h4, bullZL_d1)` if both, else whichever matched | `close + 2 × (close − SL)` |
| HTF Buy  (line 526-532) | `nweBull_h4 AND bullF_d1` | `bullZL_d1` (D1 zone low) | `close + 2 × (close − SL)` |
| LTF Sell (line 534-541) | `nweBear_1h AND (bearF_h4 OR bearF_d1)` | `max(bearZH_h4, bearZH_d1)` if both, else whichever matched | `close − 2 × (SL − close)` |
| HTF Sell (line 543-549) | `nweBear_h4 AND bearF_d1` | `bearZH_d1` (D1 zone high) | `close − 2 × (SL − close)` |

Key bindings:

- `bullZL_*` / `bearZH_*` come from `scanOBRange()` (line 134) → for Bull, the **`zoneLow` of the most recent unmitigated bullish OB / breaker-support / bullish-FVG** that overlaps the current bar. For Bear, the **`zoneHigh` of the matching bearish zone**.
- Zone heights are determined by the candle geometry at zone formation:
  - **OB zone**: `[low[i], high[i]]` of the bar where the sweep+gap pattern formed.
  - **FVG zone**: `[low[i], low[i-2 or i-3]]` (bullish) — i.e., the price gap span between bar i and bar i-2/i-3.
- ⇒ **A wide candle / wide gap at zone formation → wide zone → wide SL → wider TP (2× wider).** Same algorithm, very different absolute width depending on instrument volatility at the time of formation.

### "TP = 2 × SL" relationship

Lines 522, 531, 539, 548:

```pinescript
float tp = close01 + 2 * (close01 - sl)   // Buy
float tp = close01 - 2 * (sl - close01)   // Sell
```

This is the **intentional 2:1 raw R:R** that the SB audit confirms across 100% of the corpus. It's not an emergent property — it's a hardcoded line. Tightening or widening this would require a Pine edit; verdict (c) for the asymmetry itself.

## Per-symbol verification — live `signalSnapshot` ↔ Pine formula

I re-derived SL from each setup's snapshot `ob_fvg` payload and TP from `entry ± 2×(entry−SL)`. All three match the stored fields exactly.

### NZDUSD — Currencies — raw Sell, 77d

`signalSnapshot.ob_fvg`:
```
1H OB breaker_resistance  zoneHigh=0.59312  zoneLow=0.59162
D1 OB breaker_resistance  zoneHigh=0.60270  zoneLow=0.59285
```
- Direction = Sell, `obTf = "D1"` (D1 OB matched).
- LTF Sell branch (line 534-541), only D1 alignment → `sl = bearZH_d1 = 0.6027`.
- TP = `0.59086 − 2 × (0.6027 − 0.59086) = 0.5672` (rounding 0.56718). ✅ matches stored TP.
- **SL width = 2.00% above entry** (the D1 OB zone is tight — only 1.66% tall: 0.59285 → 0.60270). Rahul's "4.01%" was reading the **display** direction (TP↔SL swapped). Not wide in absolute forex terms.
- Verdict: **(b/c) — formula correct; OB zone is small; the perceived width is from the display flip.**

### MCO — US Stocks — raw Sell, 76d

`signalSnapshot.ob_fvg`:
```
1H OB  unmitigated           zoneHigh=477.83   zoneLow=473.94   (bearish, very tight)
H4 FVG bearish_fvg           zoneHigh=516.80   zoneLow=465.605  (bearish, 51.20 pts = 10.81% wide)
D1 OB  breaker_support       zoneHigh=471.90   zoneLow=442.70   (bullish — not used)
D1 FVG bearish_fvg           zoneHigh=513.29   zoneLow=471.90   (bearish, 41.39 pts)
```
- Direction = Sell, `obTf = "H4"`.
- LTF Sell branch, only H4 bearish alignment → `sl = bearZH_h4 = 516.80` (the H4 bearish FVG zoneHigh).
- TP = `473.47 − 2 × (516.80 − 473.47) = 473.47 − 86.66 = 386.81`. ✅
- **SL is the top of an H4 bearish FVG that is 10.81% tall.** A wide H4 FVG → wide SL.
- Why so tall? The H4 bar that formed this FVG had a wide intraday range — typical of US stocks in news-driven sessions. Pine has no per-symbol normalization (no ATR ratio cap), so it accepts the raw zone height.
- Verdict: **(b) — correct formula; input H4 FVG is genuinely wide.**

### THYROCARE — Indian Stocks — raw Buy, 58d

`signalSnapshot.ob_fvg`:
```
D1 FVG bullish_fvg  zoneHigh=455.55  zoneLow=167.56649732
```
- Direction = Buy, `obTf = "D1"`.
- Only D1 alignment → LTF Buy branch → `sl = bullZL_d1 = 167.5665`.
- TP = `348 + 2 × (348 − 167.5665) = 348 + 360.867 = 708.867`. ✅
- **The D1 bullish FVG is 287.99 INR tall (zoneLow 167.57 → zoneHigh 455.55) — equivalent to ~83% of entry price.** A single D1 candle (or sweep-gap-3-bar pattern) created this huge price gap. Pine anchors SL at the bottom of that gap.
- This is structurally the same pattern as MCO, just on a far more volatile instrument and timeframe. Same formula; extreme input.
- Verdict: **(b) — Pine ran correctly. The D1 FVG genuinely has a 287.99-INR gap; SL is correctly at its bottom.**

## Why this happens — the deeper cause

The FVG formation logic (scanOBRange, lines 186-219 for bullish OB; analogous for bullish FVG):

```pinescript
bool bullSweep = low[i] < low[i-1] and low[i] < low[i+1]   // sweep low
bool bullGap2  = high[i] < low[i-2] and high[i] < high[i-2]  // gap to bar i-2
bool bullGap3  = high[i] < low[i-3] and high[i] < high[i-3]  // gap to bar i-3
bool bullGapAtFormation = bullGap2 or bullGap3
if bullOBFormed:
    obHigh   = high[i]
    obLow    = low[i]
    gapLevel = bullGap3 ? low[i-3] : low[i-2]
    fvgTop    = gapLevel
    fvgBottom = obHigh
    fvgHeight = fvgTop - fvgBottom   // ⟵ NO CAP on this
```

There is **no width filter, no ATR ratio check, no max-zone-percentage rejection**. A daily candle with a 50% gap is just as valid as a 1% gap. For low-float Indian stocks (THYROCARE), historical wicks can produce gap-3 spans of 80%+ of price. The system trusts the gap as a "valid demand zone" regardless of width.

## Recommendations

These are TTE-side options. None are urgent — production is correct as designed. Flagging trade-offs only.

1. **Do nothing (recommended for now).** The 2:1 raw R:R is by design; SB inverts to a 73.8% display win rate (positive EV per the SB audit). Tightening SL would compress that. The wide-SL outliers (THYROCARE, AES, ATGL) are pulling the heavy tail of the distribution. No bug.
2. **Add an optional max-zone-height filter in Pine** (e.g., reject zones whose height exceeds `max_zone_pct × close01`). This would suppress emission of THYROCARE-class extreme outliers at the source. **Risk**: changes the win-rate distribution; needs SB backtest before deploy. Not a 5-min change.
3. **Surface zone height in the alert payload.** Add `zh: <zoneHeightPct>` to `buildSetupV2()` so SB / UI can sort or hide "extreme" placements. Smaller change; non-breaking.
4. **Education-only path (recommended UX response, per SB audit's option A/B):** Don't touch Pine. Add a copy / info-tip on the setup card explaining "high-win-rate, wide-SL system." Cheaper, reversible. Owner: SB.

## Questions for SB

- Is there interest in a **max-zone-height filter** on the Pine side (option 2)? Would need a backtest target — what win-rate floor to preserve?
- Should I add `zh` (zone-height-pct) to the alert payload (option 3) so SB can flag/sort extreme placements?
- Any preference between zone-height-pct vs ATR-multiple as the "extreme" metric?

## Artefacts

- Pine source: `Pine Script Code/TTE Screener V2.txt`
  - Setup branches: lines 517-583 (4 per symbol × 2 symbols)
  - OB/FVG scanner: lines 134-400+ (`scanOBRange`)
  - Alert payload: lines 503-506 (`buildSetupV2`), line 690 (`alert()`)
- Live snapshot evidence: queried from `tte.setup_messages` 2026-05-20 21:00 IST.
- Companion report: `.claude/reports/long-running-investigation-2026-05-20.md`
