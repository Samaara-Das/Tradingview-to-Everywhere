
# Tradingview to Everywhere

## What this does
Opens tradingview, opens a couple tabs and sets alerts on each of them. These alerts will be for the screener and will notify us about a new entry/exit which happened in the screener. 

Entries happen on the 1hr timeframe. This timeframe is set in Pinescript.

Then, after the alerts are set, all the tabs are closed and 1 remains open. It will be reading the alerts which come on that tab. When the alerts come, it reads the entry/exit and other info like the Symbol, Timeframe, TP, SL etc...

It goes to that particular entry's/exit's symbol and timeframe and takes a snapshot of it.

Then it sends that snapshot to a database and to Poolsifi. 

## Things to keep in mind:
- Do not move/click anything on the selenium controlled browser
- Make sure you are fine with it deleting all the alerts and creating new ones
- Make sure that any other chrome browser is closed otherwise it won't work
- Make sure that when the selenium controlled browser is opened, no other tab is manually opened
- Please use the dassamaara gmail id to login to Tradingview as the chart on that account has been set up in a specific way & it is a Pro account (this app needs to be run on a Pro account so that it can let Tradingview run on multiple tabs)
- There must be a saved layout named "Screener" which has the following setup:
    - The background has the symbol & timeframe watermark
    - The bars are medium sized and the chart is a 100 bars from the right
    - The indicators on the chart: Signal on the top and Screener below it. Screener has to be of the latest version.
    - The Alerts sidebar is open
    - The Alerts log sidebar is not minimized
    - In the alert settings, "On site Pop up" is unticked
    - The screener indicator only uses 8 symbols
    - The screener indicator must be visible
    - No popups or clicks should happen manually
