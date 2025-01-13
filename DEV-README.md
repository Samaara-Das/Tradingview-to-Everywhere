# How to start TTE

1. Follow the instructions for:
   - [Pinescript](#for-pinescript)
   - [main.py](#for-mainpy)
   - [database/local_db.py](#for-databaselocal_dbpy)
   - [resources/categories.py](#for-resourcescategoriespy)
   - [send_to_socials/send_to_discord.py](#for-send_to_socialssend_to_discordpy)
   - [open_tv.py](#for-open_tvpy)
2. Run the main.py file or start the exe file in the dist directory

# Things to keep in mind while TTE is running

## Browser

1. Do not move/click anything on the selenium controlled browser
2. Make sure you are fine with it deleting any alerts and creating new ones
3. Make sure that any other chrome browser is closed otherwise it won't work
4. Make sure that when the selenium controlled browser is opened, no other tab is manually opened

## Tradingview

1. No popups or clicks should happen manually
2. In the alert settings, "On site Pop up" is unticked
3. the "Alerts log" must be maximized (although it doesn't have to be FULLY maximized) and not minimized.
4. There must be a saved layout named "Screener" which has the following setup:
   - The bars are medium sized and the chart is a 100 bars from the right
   - Premium Screener indicator & Trade Drawer indicator should be on the chart
   - Premium Screener should have 15-20 inputs (So that Python can click on it)
5. There must be a saved layout named "Exits" and the Get Exits indicator should be on it.

## Some errors which might happen on Tradingview

1. "Modify_study_limit_exceeding" error can happen on a script whose inputs are getting changed frequently.
2. "Calculation timed out" error happens when the script exceeds the time limit for calculation
3. "Stopped - Calculation error" can happen in the alert

# Configuration

### For open_tv.py

1. Ensure that you have the `CHROME_PROFILES_PATH` User Environment Variable. The value of this variable should be the path to the chrome user data folder. Eg: `CHROME_PROFILES_PATH = 'C:\\Users\\Username\\AppData\\Local\\Google\\Chrome\\User Data'`

2. Ensure that you have a TTE folder in the chrome user data directory.

3. Ensure that the PROFILE constant in the env.py file is set to the profile (in the chrome user data directory) which you want TTE to use as the chrome profile. Please ensure that it uses the profile for the dassamaara account.

4. Ensure that you have the `TRADINGVIEW_EMAIL` and `TRADINGVIEW_PASSWORD` user environment variables. This application signs in to TradingView using them. Please ensure that you have followed the instructions below as well.

5. When changing the `TRADINGVIEW_EMAIL` and `TRADINGVIEW_PASSWORD` user environment variables, ensure that:
   - Two-factor authentication is disabled for the corresponding TradingView account (check under Settings -> Privacy and Security)
   - No social accounts are linked to the TradingView account. Check under Settings -> Privacy and Security. (if you don't see "Linked social accounts", you're good)
   - You originally created the account using email/password, not through Google or other social sign-ins
   - The email and password are for the dassamaara account as the chart on that account has been set up in a specific way for TTE to work

These steps are crucial as they allow TTE to securely sign in to TradingView using the email and password you provide.

6. `SYMBOL_INPUTS` in `open_tv.py` should be the number of inputs in the screener which will be filled with symbols by Python. There are currently a total of 20 symbol inputs in the screener. Only a couple of them will get filled (currently, only 5). So, don't give this constant a value of the total number of symbol inputs. To change how many symbols can get filled, go to the screener's code in Pine Script.

7. In `open_tv.py`, specify the timeframe of the chart. It is in the `CHART_TIMEFRAME` constant. This is the timeframe which the entries run on. The value of the constant should be a string and one of these options (The spelling must be correct):![Alt text](media/chart-tf.png)

8. In `open_tv.py`, make sure the `USED_SYMBOLS_INPUT` constant is the name of the "Used Symbols" input in the screener

9. In `open_tv.py`, make sure the `LAYOUT_NAME` constant is set to the name of the layout on Tradingview which is meant for the screener.

10. In `open_tv.py`, the constant `SCREENER_REUPLOAD_TIMEOUT` has to have a value for the number of seconds it should wait for the screener to be re-uploaded on the chart.

### For send_to_socials/send_to_discord.py

1. `BI_REPORT_LINK` should be the shortened link of the latest Trade Stats Power BI Report. Use Bitly to shorten it.

### For resources/categories.py

In Poolsifi's discord server, there are 4 categories: CURRENCIES, US STOCKS, INDIAN STOCKS and CRYPTO.
In each category, there are 3 channels: strategy-1, exits and before-and-after.
The instructions below will show you what you need to do for each category and its channels.
Note: The indices category is not used anywhere because papa told me to remove it as barely a few entries and exits are made.

**For the CURRENCIES category:**

- `CURRENCIES_WEBHOOK_NAME` in categories.py should be "Currencies".
- `CURRENCIES_ENTRY_WEBHOOK_LINK` in categories.py should be the webhook link of the strategy-1 channel.
- `CURRENCIES_EXIT_WEBHOOK_LINK` in categories.py should be the webhook link of the exits channel.
- `CURRENCIES_BEFORE_AFTER_WEBHOOK_LINK` in categories.py should be the webhook link of the before-and-after channel.

**For the US STOCKS category:**

- `US_STOCKS_WEBHOOK_NAME` in categories.py should be "US Stocks".
- `US_STOCKS_ENTRY_WEBHOOK_LINK` in categories.py should be the webhook link of the strategy-1 channel.
- `US_STOCKS_EXIT_WEBHOOK_LINK` in categories.py should be the webhook link of the exits channel.
- `US_STOCKS_BEFORE_AFTER_WEBHOOK_LINK` in categories.py should be the webhook link of the before-and-after channel.

**For the INDIAN STOCKS category:**

- `INDIAN_STOCKS_WEBHOOK_NAME` in categories.py should be "Indian Stocks".
- `INDIAN_STOCKS_ENTRY_WEBHOOK_LINK` in categories.py should be the webhook link of the strategy-1 channel.
- `INDIAN_STOCKS_EXIT_WEBHOOK_LINK` in categories.py should be the webhook link of the exits channel.
- `INDIAN_STOCKS_BEFORE_AFTER_WEBHOOK_LINK` in categories.py should be the webhook link of the before-and-after channel.

**For the CRYPTO category:**

- `CRYPTO_WEBHOOK_NAME` in categories.py should be "Crypto".
- `CRYPTO_ENTRY_WEBHOOK_LINK` in categories.py should be the webhook link of the strategy-1 channel.
- `CRYPTO_EXIT_WEBHOOK_LINK` in categories.py should be the webhook link of the exits channel.
- `CRYPTO_BEFORE_AFTER_WEBHOOK_LINK` in categories.py should be the webhook link of the before-and-after channel.

### For database/local_db.py

1. Ensure that the `MONGODB_PWD` user environment variable is set to the password of the mongodb database. To edit that password, sign in to MongoDb and go to Database Access on the left. Click on the user (i.e. sammy) and edit the password.

### For exits.py

1. `self.col` is supposed to be the name of the collection where entries are stored.
2. The keys in the `self.last_checked_dates` dictionary should be the value of the category field in MongoDB documents (i.e. Currencies, US Stocks, Crypto etc...)

### For main.py

1. `SCREENER_SHORT` is supposed to be the shorttitle of the screener.
2. `DRAWER_SHORT` is supposed to be the shorttitle of the Trade Drawer indicator.
3. `SCREENER_NAME` is supposed to be the name of the screener (the name of the script).
4. `DRAWER_NAME` is supposed to be the name of the Trade Drawer indicator (the name of the script).
5. `INTERVAL_MINUTES` has to be set to the number of minutes Python should wait until it restarts all the inactive alerts
6. `START_FRESH` is like an on/off switch for starting fresh, deleting all alerts and setting up new alerts OR just opening TradingView, keeping the pre-existing alerts and waiting for alerts to come. If it's `True`, the application will open TradingView, delete all the alerts and start setting up all 260 alerts again. If it's `False`, the application will open TradingView, NOT delete the alerts but instead keep all the alerts that were made when the application was previously run. This variable was created so that I could do 2 things:
   - When I leave the application running, come back in the morning to find it frozen and find alerts in the Alerts log that are unread by the application, I would like to re-start the application and keep the alerts that were made when it ran previously without deleting all the alerts and therefore, keeping the alerts in the Alerts log. So, when I run the application with `START_FRESH` set to `False`, the application won't delete all the alerts, read the unread alerts that came when it was previously running and wait for new alerts.
   - Sometimes, when I think I need to start fresh, delete all the alerts and make new ones, I can set `START_FRESH` set to `True`.
7. `LINES_TO_KEEP` is the number of latest lines to keep in the log file. It keeps deleting the oldest logs and keeps the latest `LINES_TO_KEEP` lines. This was done to prevent the log file from slowing down the application.

### For Pinescript

1. In the Trade Drawer indicator, in Pinescript, the first 6 inputs have to be arranged in this order: dateTime, entry, sl, tp1, tp2, tp3

2. In Pine Script, the Get Exits indicator must have its first 7 inputs in this order: `entryTime`, `entryPrice`, `entryType`, `sl`, `tp1`, `tp2`, `tp3`

3. If the symbols in `symbol_settings.py` are rare and have prices like -5.0000000034782 or 0.00000389, go to the screener and fix the code in the alertMsg function to make it convert those prices into their correct string versions. Their string versions should be the exact same as the prices and should not be rounded off and the decimal places should not be cut off.

4. The Premium Screener and the Get Exits indicators on Tradingview must to be starred (so that they can appear in the Favorites dropdown)

5. Make sure that in the `timeframeToString` function, the timeframe of the entries is mentioned under the `switch` statement. Eg: If the timeframe of the entries is 1 hour, this statement should be there: `'60' => '1 hour'`
