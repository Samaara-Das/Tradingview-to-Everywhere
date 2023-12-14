
# Tradingview to Everywhere

## Branch description
This is the multi-alert system. The development of this branch is complete. This will be used for Poolsifi.

## What this does (high level overview)
This opens Tradingview and sets it up. Then python gets a set of roughly 10 symbols from a category (the categories are Us Stocks, Indian Stocks, Crypto etc.) It changes the symbol of the chart to the 1st symbol of that set (so that an alert can get created for that symbol). Then Python goes to the screener and fills it up with all those symbols in the set. The maximum number of symbols it can fill into the screener are 10. After that, an alert gets set for the screener. This process continues until Python covers all the symbols of every category.

After alerts have been created for all the symbols, Python checks the "Alert log" for messages from the alerts it created. Every message comes from a specific alert. So, every message will have the entries which came from the screener which that specific alert was set to. There can be a single entry or multiple entries in a message.

Python then goes through each message which came. It reads each entry in that message. Python then goes to that entry's symbol and timeframe. Then it fills up the entry time, entry price, TP and SL of that entry in an indicator. That other indicator then draws the entry based on the info it has been filled up with. The drawing will look like this: ![Alt text](media/entry-drawing.png) 

Then, Python takes a snapshot of that and send it to Discord, Poolsifi and a database.

This whole process is repeated for all the messages until there are no more left. Once there are no more messages left, Python waits for them to come.

## Things to do for programmers:

### For open_tv.py
1. `SYMBOL_INPUTS` in `open_tv.py` should be the number of inputs in the screener which will be filled with symbols by Python. There are currently a total of 20 symbol inputs in the screener. Only a couple of them will get filled (currently, 10 of them will get filled). So, don't give this constant a value of the total symbol inputs. To change how many symbols can get filled, go to the screener's code.

2. In `open_tv.py`, specify the timeframe of the chart. It is in the `CHART_TIMEFRAME` constant. This is the timeframe which the chart runs on. Keep it to "1 minute" so that all 216 alerts can load. If the chart timeframe is on a higher timeframe, a couple of alerts would fail to get created. The value of the constant should be a string and one of these options (The spelling must be correct):![Alt text](media/chart-tf.png) 

3. In `open_tv.py`, specify the timeframe of the screener. The timeframe of the screener is the "Timeframe" input in the screener which controls the timeframe of the entries. It is in the `SCREENER_TIMEFRAME` constant. It should be a string and one of these options (The spelling must be correct): ![Alt text](media/screener-tf.png)

4. In `open_tv.py`, make sure the `USED_SYMBOLS_INPUT` constant is the name of the "Used Symbols" input in the screener

5. In `open_tv.py`, make sure the `LAYOUT_NAME` constant is set to the name of the layout on Tradingview which is meant for the screener.

6. In `open_tv.py`, the constant `SCREENER_REUPLOAD_TIMEOUT` has to have a value for the number of seconds it should wait for the screener to be re-uploaded on the chart. 

### For resources/categories.py
1. `CURRENCIES_WEBHOOK_NAME` should be the name of the webhook which is for the channel where forex snapshots are supposed to go. `CURRENCIES_WEBHOOK_LINK` should be the link of that webhook.

2. `US_STOCKS_WEBHOOK_NAME` should be the name of the webhook which is for the channel where Us Stocks snapshots are supposed to go. `US_STOCKS_WEBHOOK_LINK` should be the link of that webhook.

3. `INDIAN_STOCKS_WEBHOOK_NAME` should be the name of the webhook which is for the channel where Indian Stocks snapshots are supposed to go. `INDIAN_STOCKS_WEBHOOK_LINK` should be the link of that webhook.

4. `CRYPTO_WEBHOOK_NAME` should be the name of the webhook which is for the channel where Crypto snapshots are supposed to go. `CRYPTO_WEBHOOK_LINK` should be the link of that webhook.

5. `INDICES_WEBHOOK_NAME` should be the name of the webhook which is for the channel where Indices snapshots are supposed to go. `INDICES_WEBHOOK_LINK` should be the link of that webhook.

### For database/local_db.py
1. `PWD` is supposed to be the password of our remote database. To edit that password, sign in to MongoDb and go to Data/base Access on the left. Click on the user (i.e. sammy) and edit the password.

### For main.py
1. `SCREENER_SHORT` is supposed to be the shorttitle of the screener.
2. `DRAWER_SHORT` is supposed to be the shorttitle of the Trade Drawer indicator.
3. `SCREENER_NAME` is supposed to be the name of the screener (the name of the script).
4. `DRAWER_NAME` is supposed to be the name of the Trade Drawer indicator (the name of the script).
5. `INTERVAL_MINUTES` has to be set to the number of minutes Python should wait until it restarts all the inactive alerts

### For Pinescript
1. Premium Screener can have only 1 input which opens a dropdown. That is the Timeframe input. It has to be this way so that the Timeframe input can be found in `change_screener_timeframe` in `open_tv.py`

2. In the Trade Drawer indicator, in Pinescript, the first 6 inputs have to be arranged in this order: dateTime, entry, sl, tp1, tp2, tp3

3. If the symbols in `symbol_settings.py` are rare and have prices like -5.0000000034782 or 0.00000389, go to the screener and fix the code in the alertMsg function to make it convert those prices into their correct string versions. Their string versions should be the exact same as the prices and should not be rounded off and the decimal places should not be cut off.

4. The Premium Screener indicator on Tradingview has to be starred (so that it can appear in the Favorites dropdown)

## Some errors which might happen on Tradingview
1. "Modify_study_limit_exceeding" error can happen on a script whose inputs are getting changed frequently. 
2. "Calculation timed out" error happens when the script exceeds the time limit for calculation
3. "Stopped - Calculation error" can happen in the alert

## Browser
1. Do not move/click anything on the selenium controlled browser
2. Make sure you are fine with it deleting any alerts and creating new ones
3. Make sure that any other chrome browser is closed otherwise it won't work
4. Make sure that when the selenium controlled browser is opened, no other tab is manually opened

## Tradingview
1. Please use the dassamaara gmail id to login to Tradingview as the chart on that account has been set up in a specific way
2. No popups or clicks should happen manually
3. In the alert settings, "On site Pop up" is unticked
4. the "Alerts log" must be maximized (although it doesn't have to be FULLY maximized) and not minimized. 
5. There must be a saved layout named "Screener" which has the following setup:
    - The bars are medium sized and the chart is a 100 bars from the right 
    - Premium Screener indicator & Trade Drawer indicator should be on the chart
    - Premium Screener should have 15-20 inputs (So that Python can click on it)
    
