# Tradingview to Everywhere

## What this does
TradingView to Everywhere (TTE) automatically creates posts about trading entries and exits and publishes them to various social media platforms. 

## Detailed description
To post about trading entries, TTE goes to the TradingView website. It scrapes notifications about new trading entries across 1,300+ financial instruments. These notifications are generated through a custom indicator that I built on TradingView. These notifications contain information about an entry like it's entry and exit levels, the time it started, which instrument it got generated on etc. TTE uses this information to visualize each entry using TradingView's drawing tools. After that, a screenshot is taken of each entry. The screenshot along with information about the respective entry is posted to Discord, [Facebook](https://www.facebook.com/profile.php?id=61556913881911), [X (Twitter)](https://x.com/MarketDavinci) and [Poolsifi (my startup's website where these entries are displayed)](https://poolsifi.com/pool/setup). These entries are also simultaneously being stored on MongoDB.

To post about trading exits, TTE periodically checks if any of the trading entries have hit their exit levels. It starts with accessing these entries from MongoDB. Then, it inputs each entry to another custom indicator which checks if the given entry has hit its exit levels. If the entry has, the exit of the entry is visualized using TradingView's drawing tools and a screenshot is taken of it. That, along with informatin about the exit, is posted to Discord, [Facebook](https://www.facebook.com/profile.php?id=61556913881911), [X (Twitter)](https://x.com/MarketDavinci) and [Poolsifi (my startup's website where these entries are displayed)](https://poolsifi.com/pool/setup).

This system works 24/7. TradingView has no API for TTE to access these trading signals so it instead utilizes web automation to access them and visualize them. Check out [the statistics](https://bit.ly/trade-stats) of the trading signals.
