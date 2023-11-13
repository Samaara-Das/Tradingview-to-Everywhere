
# Tradingview to Everywhere

## What this does
Opens tradingview, opens a couple tabs and sets alerts on each of them. These alerts will be for the screener and will notify us about a new entry/exit which happened in the screener. 

Entries happen on the 1hr timeframe. This timeframe is set in Pinescript.

Then, after the alerts are set, all the tabs are closed and 1 remains open. It will be reading the alerts which come on that tab. When the alerts come, it reads the entry/exit and other info like the Symbol, Timeframe, TP, SL etc...

It goes to that particular entry's/exit's symbol and timeframe and takes a snapshot of it.

Then it sends that snapshot to a database and to Poolsifi. 

## Things to do for programmers:
- In `main.py`, specify the indicators' short-titles. They are currently: "Trade" and "Screener". These names will be used to find the indicators
- In `main.py`, specify the screener indicator's & trade drawer indicator's script names. It is currently "Premium Screener"
- `SYMBOL_INPUTS` in `open_tv.py` should be the same as the number of symbol inputs in the screener

## Some errors which might happen
- "Modify_study_limit_exceeding" error can happen on a pinescript script whose inputs are getting changed frequently. 
- "Calculation timed out" error happens when the script was calculating for a long time.

### Browser
- Do not move/click anything on the selenium controlled browser

- Make sure you are fine with it deleting all the alerts and creating new ones

- Make sure that any other chrome browser is closed otherwise it won't work

- Make sure that when the selenium controlled browser is opened, no other tab is manually opened

### Tradingview
- Please use the dassamaara gmail id to login to Tradingview as the chart on that account has been set up in a specific way

- There must be a saved layout named "Screener" which has the following setup:
    - The background has the symbol & timeframe watermark
    - The bars are medium sized and the chart is a 100 bars from the right 
    - In the alert settings, "On site Pop up" is unticked
    - Premium Screener indicator and Trade Drawer indicator should be on the chart
    - Premium Screener should have 15 inputs for the symbols
    - No popups or clicks should happen manually
