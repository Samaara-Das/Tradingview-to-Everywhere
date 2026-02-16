# Kernel AO Divergence - Logic 2 Detailed Analysis

## Overview

This indicator detects **divergences** between price action and momentum using a custom oscillator built from two Nadaraya-Watson kernel regression lines. "Logic 2" is one of two divergence detection methods in the indicator. It identifies moments where price is moving in one direction but the underlying momentum is moving in the opposite direction, suggesting a potential reversal or continuation.

This document covers only the Logic 2 divergence system and the components it depends on.

## What is the Kernel AO Oscillator?

The Kernel AO (Awesome Oscillator) is a momentum oscillator that measures the difference between a fast-reacting and a slow-reacting kernel regression line. Think of it like a MACD, but instead of using Exponential Moving Averages, it uses Nadaraya-Watson Rational Quadratic Kernel regression lines, which produce a significantly smoother and more adaptive curve.

The fast kernel line reacts quickly to recent price changes (lookback of 5 bars), while the slow kernel line captures the broader trend (lookback of 34 bars). When the fast line is above the slow line, the oscillator is positive (bullish momentum). When the fast line is below the slow line, the oscillator is negative (bearish momentum).

This oscillator is the foundation for everything in Logic 2. The crossovers of the oscillator between positive and negative territory define the "ranges" that the divergence detection relies on.

## What is a "Range" and Why Does It Matter?

A "range" is a continuous period where the oscillator stays on one side of zero. A **positive range** is the period where the oscillator is above zero (bullish momentum), and a **negative range** is the period where the oscillator is below zero (bearish momentum).

These ranges are important because they represent complete momentum cycles. Each time the oscillator crosses zero, a new range begins and the previous range is "locked in." The indicator uses these ranges to define the legs of price movement and to compare momentum strength between consecutive legs.

## How Are Swing Highs and Lows Identified?

The indicator identifies swing highs and lows based on the oscillator's ranges rather than traditional price pivots. During each positive range (bullish momentum), the indicator tracks the highest price reached on the chart. During each negative range (bearish momentum), it tracks the lowest price reached. When the oscillator crosses zero and a new range begins, the previous extreme becomes a confirmed swing point.

This creates an alternating sequence of swing highs and swing lows that are directly tied to momentum cycles:
- **Swing High**: the highest price during a positive oscillator range (bullish momentum peak)
- **Swing Low**: the lowest price during a negative oscillator range (bearish momentum trough)

The indicator always maintains the two most recent swing highs and the two most recent swing lows. These four points are what Logic 2 uses to detect divergences.

## What is a "Leg" in This Context?

A "leg" describes the current direction of the swing structure:
- **Upleg**: the most recent swing point is a high (price has been moving up from a low to a high)
- **Downleg**: the most recent swing point is a low (price has been moving down from a high to a low)

Logic 2 only looks for bullish divergences during downlegs and bearish divergences during uplegs. This ensures that divergences are detected at the right structural moment, not in the middle of a move.

## What is Divergence?

Divergence occurs when price and momentum disagree. If price makes a new extreme but the oscillator does not confirm it, the move may be losing steam. There are four types of divergence that Logic 2 detects:

**Regular Divergence** signals a potential reversal of the current trend.
**Hidden Divergence** signals a potential continuation of the current trend.

## How Does Logic 2 Detect Regular Bullish Divergence?

Regular bullish divergence occurs during a downleg when price is making lower lows but momentum is making higher lows. This suggests that even though price is falling, the selling pressure is weakening, which often precedes a reversal to the upside.

The indicator compares two negative oscillator ranges (downleg momentum cycles):
1. The **previous downleg**: the negative oscillator range that occurred between the current swing high and the previous swing low
2. The **current downleg**: the negative oscillator range from when the oscillator most recently crossed below zero to the present bar

For each range, the indicator finds the most negative oscillator value (the deepest point of bearish momentum). If:
- Price at the current swing low is **lower** than price at the previous swing low (lower low in price)
- But the current downleg's deepest oscillator value is **less negative** than the previous downleg's (higher low in momentum)

Then regular bullish divergence is detected. A line is drawn on the chart connecting the two price lows in pink/magenta.

**What it looks like conceptually:**
- Price is falling to new lows (bearish on the surface)
- But each successive drop has less bearish momentum behind it
- The market is losing selling conviction, suggesting a potential bullish reversal

## How Does Logic 2 Detect Hidden Bullish Divergence?

Hidden bullish divergence occurs during a downleg when price is making higher lows but momentum is making lower lows. This suggests the existing bullish trend is likely to continue despite a temporary increase in selling pressure.

The same two negative oscillator ranges are compared, but with opposite conditions:
- Price at the current swing low is **higher** than the previous swing low (higher low in price, maintaining bullish structure)
- But the current downleg's deepest oscillator value is **more negative** than the previous downleg's (lower low in momentum)

A line is drawn connecting the two price lows in dark magenta.

**What it looks like conceptually:**
- Price is holding higher lows (bullish structure intact)
- Momentum dipped deeper into bearish territory on the latest pullback
- Despite the stronger pullback in momentum, the trend structure held, suggesting bullish continuation

## How Does Logic 2 Detect Regular Bearish Divergence?

Regular bearish divergence occurs during an upleg when price is making higher highs but momentum is making lower highs. This suggests that even though price is rising, the buying pressure is weakening.

The indicator compares two positive oscillator ranges (upleg momentum cycles):
1. The **previous upleg**: the positive oscillator range that occurred between the current swing low and the previous swing high
2. The **current upleg**: the positive oscillator range from when the oscillator most recently crossed above zero to the present bar

For each range, the indicator finds the most positive oscillator value (the peak of bullish momentum). If:
- Price at the current swing high is **higher** than the previous swing high (higher high in price)
- But the current upleg's peak oscillator value is **less positive** than the previous upleg's (lower high in momentum)

Then regular bearish divergence is detected. A line is drawn connecting the two price highs in pink/magenta.

**What it looks like conceptually:**
- Price is pushing to new highs (bullish on the surface)
- But each successive push has less bullish momentum behind it
- The market is losing buying conviction, suggesting a potential bearish reversal

## How Does Logic 2 Detect Hidden Bearish Divergence?

Hidden bearish divergence occurs during an upleg when price is making lower highs but momentum is making higher highs. This suggests the existing bearish trend is likely to continue.

The same two positive oscillator ranges are compared, but with opposite conditions:
- Price at the current swing high is **lower** than the previous swing high (lower high in price, maintaining bearish structure)
- But the current upleg's peak oscillator value is **more positive** than the previous upleg's (higher high in momentum)

A line is drawn connecting the two price highs in dark magenta.

**What it looks like conceptually:**
- Price is making lower highs (bearish structure intact)
- Momentum pushed higher on the latest rally attempt
- Despite the stronger rally in momentum, price failed to make a new high, suggesting bearish continuation

## How Does Logic 2 Differ from Logic 1?

Logic 1 and Logic 2 both detect divergence using the same Kernel AO Oscillator, but they identify swing points differently:

**Logic 1** uses a traditional Zigzag indicator to find price pivots. The zigzag is based on configurable depth, deviation, and backstep parameters. It then checks whether the oscillator ranges between those zigzag pivots show divergence. Logic 1 tracks and compares multiple oscillator ranges over a longer history, building arrays of ranges to find the most significant divergence across many cycles.

**Logic 2** uses the oscillator's own positive/negative cycles to define swing points. The swings are inherently tied to momentum rather than price structure alone. Logic 2 only compares the two most recent legs (previous vs. current), making it more responsive but limited to recent price action.

In practice, Logic 1 may detect divergences that span many momentum cycles (longer-term structural divergence), while Logic 2 focuses on the most immediate momentum shift between consecutive legs.

## What Does the Indicator Draw on the Chart?

**Swing High/Low Legs** (cyan by default): Zigzag-style lines connecting alternating swing highs and swing lows. These lines show the oscillator-defined price structure and update in real-time as new extremes are found within the current range.

**Regular Divergence Lines** (pink/magenta by default): Lines connecting the two price points where regular divergence was detected. For bullish divergence, the line connects two swing lows. For bearish divergence, the line connects two swing highs.

**Hidden Divergence Lines** (dark magenta by default): Same as regular divergence lines but for hidden divergence, drawn in a darker color to distinguish them.

When a new divergence is detected from the same starting swing point as an existing divergence line, the old line is replaced with the updated one. This prevents multiple lines from stacking on top of each other.

## Does This Indicator Repaint?

The swing points and divergence lines update in real-time as the current oscillator range develops. A swing high or low is only "confirmed" when the oscillator crosses zero and a new range begins. Until that happens, the current swing point may shift if a new extreme is reached within the current range.

This means divergence lines can appear and then adjust or disappear as the current range develops. Once the oscillator crosses zero and the range completes, the swing point and any associated divergence become stable.

## Signals

**Regular Bullish Divergence** - when a divergence line appears connecting two swing lows, with the right low being lower than the left. Signifies weakening selling pressure during a downtrend, suggesting a potential bullish reversal.

**Hidden Bullish Divergence** - when a divergence line appears connecting two swing lows, with the right low being higher than the left. Signifies bullish trend continuation despite a temporary momentum dip.

**Regular Bearish Divergence** - when a divergence line appears connecting two swing highs, with the right high being higher than the left. Signifies weakening buying pressure during an uptrend, suggesting a potential bearish reversal.

**Hidden Bearish Divergence** - when a divergence line appears connecting two swing highs, with the right high being lower than the left. Signifies bearish trend continuation despite a temporary momentum surge.
