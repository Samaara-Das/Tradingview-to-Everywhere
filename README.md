
# Tradingview screenshots to twitter

## This is a work in progress...

This project is for Poolsifi. This will send screenshots of charts (where an entry/exit happened) to Twitter.
An alert will notify the app that a screenshot has to be taken.

Things to keep in mind:

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
- make sure that any other chrome browser is closed otherwise it wont work
- please use the dassamaara gmail id to login to tradingview as the chart on that account has been set up in a specific way & it is a pro account (this app needs to be run on a pro account so that it can let tradingview run on multiple tabs)
    - the background has the symbol & timeframe watermark
    - the bars are a medium sized and are a 100 bars from the right
    - the indicators on the chart: Signal on the top and Screener below it. Screener has to be of version 320
    - the alerts sidebar is open
    - the alert log tag is not minimized
    - there are currently no active alerts
    - in the alert settings, "On site Pop up" is not ticked
    - the screener indicator only uses 8 symbols
    - the screener indicator must be visible
    - no popups or clicks should happen manually
- make sure that when the selenium controlled browser is opened, no other tab is manually opened