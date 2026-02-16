# Nadaraya-Watson Envelope (NWE) - Detailed Analysis

## Overview

The Nadaraya-Watson Envelope (NWE) is an advanced price envelope indicator that identifies overbought and oversold zones using kernel regression instead of traditional moving averages. It draws a smoothed price estimation line surrounded by upper and lower bands, creating zones that highlight when price has moved to statistical extremes.

## What is Nadaraya-Watson Regression?

Nadaraya-Watson Regression is a type of Kernel Regression, which is a non-parametric method for estimating the curve of best fit for a dataset. Unlike Linear Regression or Polynomial Regression, Kernel Regression does not assume any underlying distribution of the data. For estimation, it uses a kernel function, which is a weighting function that assigns a weight to each data point based on how close it is to the current point. The computed weights are then used to calculate the weighted average of the data points.

## How is This Different from Using a Moving Average?

A Simple Moving Average is actually a special type of Kernel Regression that uses a Uniform (Rectangular) Kernel function. This means that all data points in the specified lookback window are weighted equally. In contrast, the Rational Quadratic Kernel function used in this indicator assigns a higher weight to data points that are closer to the current point. This means that the indicator will react more quickly to changes in the data while still maintaining a smooth curve.

Traditional envelope indicators like Bollinger Bands or Keltner Channels use a moving average as their centerline. The NWE replaces this with kernel regression, producing a centerline that is smoother, more adaptive, and less prone to lag than any conventional moving average.

## Why Use the Rational Quadratic Kernel over the Gaussian Kernel?

The Gaussian Kernel is one of the most commonly used Kernel functions and is used extensively in many Machine Learning algorithms due to its general applicability across a wide variety of datasets. The Rational Quadratic Kernel can be thought of as a Gaussian Kernel on steroids; it is equivalent to adding together many Gaussian Kernels of differing length scales. This allows the user even more freedom to tune the indicator to their specific needs.

The formula for the Rational Quadratic function is:
K(x, x') = (1 + ||x - x'||^2 / (2 * alpha * h^2))^(-alpha)

Where x and x' are data points, alpha is a hyperparameter that controls the smoothness (i.e. overall "wiggle") of the curve, and h is the band length of the kernel.

## How Are the Envelope Bands Calculated?

The NWE applies kernel regression separately to the close, high, and low prices. This produces three smoothed lines. From these, it calculates a special ATR (Average True Range) that measures volatility based on the kernel-smoothed values rather than raw prices. This is important because it means the band width adapts smoothly to changing volatility rather than reacting sharply to individual price spikes.

The bands are then constructed by placing them at fixed ATR multiples above and below the kernel regression centerline:

**Upper Bands (Overbought Zones):**
- **Upper Near**: Centerline + 1.5x Kernel ATR (inner overbought boundary)
- **Upper Average**: Midpoint between Near and Far
- **Upper Far**: Centerline + 8.0x Kernel ATR (extreme overbought boundary)

**Lower Bands (Oversold Zones):**
- **Lower Near**: Centerline - 1.5x Kernel ATR (inner oversold boundary)
- **Lower Average**: Midpoint between Near and Far
- **Lower Far**: Centerline - 8.0x Kernel ATR (extreme oversold boundary)

This creates three distinct zones on each side: a near zone (moderately extreme), an average zone (significantly extreme), and a far zone (extremely rare price levels).

## Why Use Kernel-Smoothed ATR Instead of Regular ATR?

Standard ATR reacts to every individual candle, including noise and random spikes. By calculating ATR on the kernel-smoothed price series instead, the volatility measurement is consistent with the smoothed centerline. This produces band boundaries that expand and contract gradually rather than whipping back and forth, giving cleaner and more reliable overbought/oversold zones.

## What Do the Zones Mean?

The envelope creates a visual map of where price sits relative to its statistically expected range:

**Upper Far Zone** (between Upper Far and Upper Average): Price is at an extreme overbought level, far from the mean. This is a rare condition and often signals that price has overextended to the upside.

**Upper Near Zone** (between Upper Average and Upper Near): Price is moderately overbought. This is more common than the far zone but still indicates price is stretched above its expected value.

**Neutral Zone** (between Upper Near and Lower Near): Price is within its normal range relative to the kernel regression estimate. No extreme conditions.

**Lower Near Zone** (between Lower Near and Lower Average): Price is moderately oversold. Indicates price is stretched below its expected value.

**Lower Far Zone** (between Lower Average and Lower Far): Price is at an extreme oversold level, far from the mean. Often signals that price has overextended to the downside.

## How Does the Centerline Color Work?

The kernel regression centerline changes color based on its direction:
- **Green**: The estimate is rising compared to the previous bar, indicating a bullish regime
- **Red**: The estimate is falling compared to the previous bar, indicating a bearish regime

This color change is a simple but powerful signal on its own, representing shifts between bullish and bearish market regimes as determined by the kernel regression.

## What Are the Key Settings?

**Lookback Window** (default: 8): Controls how many recent bars influence the kernel estimate. Lower values make the curve more reactive; higher values make it smoother. Recommended range: 3-50.

**Relative Weighting** (default: 8.0): Controls the balance between short-term and long-term influence. As this value approaches zero, longer timeframes exert more influence. As it approaches infinity, the Rational Quadratic Kernel behaves identically to a Gaussian Kernel. Recommended range: 0.25-25.

**Start Regression at Bar** (default: 25): Skips the first N bars of the chart, which are often highly volatile and can distort the overall fit. Recommended range: 5-25.

**ATR Length** (default: 60): The smoothing period for the kernel-based ATR calculation. Higher values produce more stable band widths.

**Near ATR Factor** (default: 1.5): Multiplier for the inner bands. Recommended range: 0.5-2.0.

**Far ATR Factor** (default: 8.0): Multiplier for the outer bands. Recommended range: 6.0-8.0.

## Does This Indicator Repaint?

No, this indicator has been intentionally designed to NOT repaint. Once a bar has closed, the indicator will never change the values in its plot. This is useful for backtesting and for trading strategies that require a non-repainting indicator.

## Signals

**Buy signal** - when price touches or enters the lower band zones (between Lower Near and Lower Far). The deeper into the lower zones price reaches, the stronger the oversold signal. The strongest buy signals occur when price reaches the Lower Far zone while the centerline is green (bullish regime).

**Sell signal** - when price touches or enters the upper band zones (between Upper Near and Upper Far). The deeper into the upper zones price reaches, the stronger the overbought signal. The strongest sell signals occur when price reaches the Upper Far zone while the centerline is red (bearish regime).

**Regime change (bullish)** - when the centerline changes color from red to green. Signifies a bearish to bullish trend change in the kernel estimate.

**Regime change (bearish)** - when the centerline changes color from green to red. Signifies a bullish to bearish trend change in the kernel estimate.
