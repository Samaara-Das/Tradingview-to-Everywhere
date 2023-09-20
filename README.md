
# Tradingview to Everywhere

## What this does
Opens tradingview, opens a couple tabs and sets alerts on each of them. These alerts will be for the screener and will notify us about a new entry, exit which happened in the screener. 

Entries happen on the 1hr timeframe. This timeframe is set in Pinescript

Then all the tabs are closed and 1 remains open. It will be reading the alerts which come on that tab. When the alerts come, it reads the entry/exit and other info like the symbol, timeframe, tp, sl etc...

It goes to that particular entry's/exit's symbol and timeframe and takes a snapshot of it.

Then it sends that snapshot to Nishant uncle's webhook and my local database. It also sends that along with the snapshot to the database.

## Things to keep in mind:
- when using our **desktop**, use this to open the chrome profile:
    ```
    CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'

    # put this in the __init__ method
    # if google asks to sign in, just sign in manually (it's just a 1 time thing)
    chrome_options.add_argument('--profile-directory=Profile 2')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    ```

- when using our **home laptop**, use this to open the chrome profile:
    ```
    CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'

    # put this in the __init__ method
    # if google asks to sign in, just sign in manually (it's just a 1 time thing)
    chrome_options.add_argument('--profile-directory=Profile 1')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    ```

- do not move/click anything on the selenium controlled browser
- make sure you are fine with it deleting all the alerts and creating new ones
- make sure that any other chrome browser is closed otherwise it won't work
- make sure that when the selenium controlled browser is opened, no other tab is manually opened
- please use the dassamaara gmail id to login to tradingview as the chart on that account has been set up in a specific way & it is a pro account (this app needs to be run on a pro account so that it can let tradingview run on multiple tabs):
    - there must be a saved layout named "Screener" which has the following setup
    - the background has the symbol & timeframe watermark
    - the bars are a medium sized and are a 100 bars from the right
    - the indicators on the chart: Signal on the top and Screener below it. Screener has to be of the latest version
    - the alerts sidebar is open
    - the alert log tag is not minimized
    - in the alert settings, "On site Pop up" is not ticked
    - the screener indicator only uses 8 symbols
    - the screener indicator must be visible
    - no popups or clicks should happen manually