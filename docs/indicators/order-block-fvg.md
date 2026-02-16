# Order Block & Fair Value Gap (OB & FVG) Indicator - Detailed Analysis

## Overview

This indicator detects **Order Blocks** and **Fair Value Gaps** based on Smart Money Concepts (SMC). It identifies institutional supply and demand zones where significant buying or selling occurred, tracks how price interacts with those zones over time, and shows the price gaps left behind by impulsive institutional moves.

## What is an Order Block?

An Order Block (OB) is the last opposing candle before a strong directional move, representing the zone where institutional traders accumulated or distributed positions. When large institutions enter the market, they leave behind a footprint in the form of these zones. Price often returns to these zones later, where the institutions may defend their positions, causing support or resistance.

**Two Types of Order Blocks:**
1. **Bullish Order Block (Demand Zone)**: The last down-candle before an impulsive upward move. This is where institutions were buying heavily, creating demand that may attract price back to the zone later.
2. **Bearish Order Block (Supply Zone)**: The last up-candle before an impulsive downward move. This is where institutions were selling heavily, creating supply that may push price away from the zone later.

## What is a Fair Value Gap?

A Fair Value Gap (FVG) is a gap in price where no trading occurred between two non-adjacent candles. When price moves impulsively in one direction, it can leave behind a gap that the market may later try to "fill." FVGs represent inefficiency in price delivery and are closely associated with order blocks.

Every order block in this indicator has an associated FVG that represents the price gap created by the impulsive move away from the OB zone. The FVG is drawn as a separate rectangle adjacent to the order block.

## How Are Order Blocks Detected?

The indicator uses a three-step process to identify genuine institutional order blocks:

**Step 1: Gap Detection**
The indicator looks for a price gap between candles, which indicates strong directional momentum. For a bullish OB, the current candle must gap up significantly above the OB candle, leaving a void below. For a bearish OB, the current candle must gap down below the OB candle, leaving a void above. The gap must maintain proper market structure, meaning the move must be decisively in one direction.

**Step 2: Liquidity Sweep Validation**
After finding a gap, the indicator checks if the potential OB candle "swept" liquidity by poking beyond its neighboring candles. For a bullish OB, the candle must have swept below both adjacent candles, suggesting stop-loss hunting of long positions before the upward move. For a bearish OB, the candle must have swept above both adjacent candles, suggesting stop-loss hunting of short positions before the downward move. This sweep is a hallmark of institutional activity.

**Step 3: Confirmation at Multiple Distances**
The indicator checks for OB formation at two distances from the current bar:
- **Standard detection**: The OB candle is 2 bars before the current bar
- **Extended detection**: The OB candle is 3 bars before the current bar

This dual detection catches OBs that might be missed due to consolidation or multi-candle formations between the sweep and the gap. OBs detected at the extended distance are displayed in a slightly different color to distinguish them.

## How Does the FVG Relate to the Order Block?

Each OB has an FVG that represents the "gap" created by the impulsive move:

- **Bullish OB**: The FVG sits directly above the order block rectangle. It spans from the top of the OB candle up to the bottom of the current candle that confirmed the gap. This is the price void left behind as price moved impulsively upward.
- **Bearish OB**: The FVG sits directly below the order block rectangle. It spans from the bottom of the OB candle down to the top of the current candle that confirmed the gap.

The FVG is drawn as a shorter rectangle than the OB itself, highlighting just the gap area.

## What Are the Four States of an Order Block?

Order blocks evolve through different states based on how price interacts with them over time. Understanding these states is critical for using the indicator effectively.

**1. Active**
A newly formed OB that has not been significantly tested by price. It acts as potential support (bullish) or resistance (bearish). These are the "fresh" zones where institutional positions may still be defended. Bullish active OBs are shown in blue or purple; bearish active OBs are shown in red or maroon.

**2. Tested**
Price has returned to the OB zone and shown a reaction, suggesting the institutional level held. The testing process uses a two-step validation (described below) to confirm that the OB genuinely provided support or resistance rather than just being touched in passing. Tested bullish OBs turn yellow; tested bearish OBs turn green.

**3. Breaker**
The OB has been violated, meaning price closed decisively through the zone. When this happens, the zone's role reverses: a former bullish OB (demand/support) becomes **breaker resistance**, and a former bearish OB (supply/resistance) becomes **breaker support**. This is a key concept in Smart Money trading. When institutions fail to defend a level, the trapped traders on the wrong side create a new zone of interest in the opposite direction. Breaker resistance is shown in red; breaker support is shown in blue.

**4. Reversed**
The breaker block itself has been violated by price closing back through it in the original direction. This means the zone has been completely invalidated and is no longer considered significant. Reversed OBs are shown in faded black and can optionally be hidden from the chart.

The full lifecycle is: Active -> Tested (optional) -> Breaker -> Reversed

## How Does the Testing Mechanism Work?

The indicator uses a sophisticated two-step process to confirm that an order block has been properly tested, inspired by professional trading platform methodologies:

**Step 1: Price Reaches the Test Level**
A test threshold is calculated as a percentage into the OB candle's range (default: 30%). For a bullish OB, price must dip below this threshold. For a bearish OB, price must rise above it. Simply touching the edge of the OB is not enough; price must penetrate meaningfully into the zone.

**Step 2: Price Shows Rejection**
After reaching the test level, the OB is only marked as "tested" when price shows that the level held. For a bullish OB, this means price stays above or recovers back above the OB's low. For a bearish OB, this means price stays below or recovers back below the OB's high. A quick wick through with recovery counts as a successful test.

This two-step process ensures that OBs are only marked as tested when they genuinely provided support or resistance, not just because price briefly touched the zone while falling through it.

## What Are Breaker Blocks and Why Do They Matter?

A breaker block forms when an order block fails. This is one of the most powerful concepts in Smart Money trading because it represents a zone where traders are trapped on the wrong side of the market.

**How a Breaker Forms:**
1. An institutional OB is established (for example, a bullish demand zone)
2. Traders enter long positions at the zone, expecting it to hold
3. Price closes below the OB, invalidating the demand zone and trapping the long traders
4. The zone now acts as resistance because the trapped long traders will sell to exit their losing positions when price returns to the zone

**Why Breakers Provide High-Probability Trades:**
- They represent zones where trapped traders will exit positions
- Institutional traders often use these levels for new entries in the opposite direction
- The invalidation level is clear (the original OB extreme), providing a logical stop-loss placement

## How Does FVG Fill Detection Work?

The indicator tracks whether each Fair Value Gap has been "filled" by price action. An FVG is considered filled when price penetrates a configurable percentage (default: 50%) into the gap from the opposite side:

- **Bullish FVG Fill**: Price wicks downward into the gap, reaching at least 50% of the gap's height from the top
- **Bearish FVG Fill**: Price wicks upward into the gap, reaching at least 50% of the gap's height from the bottom

When an FVG is filled, it changes color to gray, indicating the inefficiency has been partially or fully resolved. A dashed line marks the fill threshold level before the fill occurs.

## What Do the Colors Mean?

**Order Block Colors:**
- Blue: Active bullish OB (standard detection)
- Purple: Active bullish OB (extended detection)
- Red: Active bearish OB (standard detection)
- Maroon: Active bearish OB (extended detection)
- Yellow: Tested bullish OB
- Green: Tested bearish OB
- Red border: Breaker resistance (former bullish OB)
- Blue border: Breaker support (former bearish OB)
- Faded black: Reversed OB (fully invalidated)

**FVG Colors:**
- Lime: Unfilled bullish FVG
- Orange: Unfilled bearish FVG
- Gray: Filled FVG

## Trading Applications

### Entry Strategies

**Fresh OB Entry**: Enter when price returns to an untested OB for the first time. This is the most aggressive approach with the highest reward potential but also the highest risk that the OB may not hold.

**Tested OB Entry**: Enter at OBs that have been tested and held at least once. More conservative with proven support/resistance. Lower reward but higher probability.

**Breaker Block Entry**: Enter when price retests a breaker block in the new direction. High probability due to trapped trader dynamics. The original OB extreme provides a clear invalidation level for stop-loss placement.

### Risk Management

- **Regular OB**: Place stop-loss beyond the OB extreme (below the low for bullish, above the high for bearish)
- **Tested OB**: Tighter stop possible due to the proven level
- **Breaker Block**: Stop beyond the breaker level in the direction of invalidation

## Does This Indicator Repaint?

The order blocks are detected with a delay of 2-3 bars to confirm the gap and sweep conditions. Once an OB is identified and drawn, it does not change retroactively. However, the state of an OB (active, tested, breaker, reversed) updates in real-time as price interacts with the zone on subsequent bars.

## Signals

**Buy signal** - when the close price of the current bar overlaps any bullish OB or breaker support OB. "Overlap" means that the current close price is at or below the top level of an OB and at or above the bottom level of an OB.

**Sell signal** - when the close price of the current bar overlaps any bearish OB or breaker resistance OB. "Overlap" means that the current close price is at or below the top level of an OB and at or above the bottom level of an OB.
