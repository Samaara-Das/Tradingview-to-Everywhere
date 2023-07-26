
# Tradingview screenshots to twitter

## This is a work in progress...

This project is for Poolsifi. This will send screenshots of charts (where an entry happened) to Twitter.
Something will notify it that a screenshot has to be taken.

Things to keep in mind:

- when using our **desktop**, use this to open the chrome profile:
    ```
    CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
    DRIVER_PATH = 'C:\\Users\\Puja\\chromedriver'

    # put this in the __init__ method
    chrome_options.add_argument('--profile-directory=Profile 5')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    ```

- when using our **home laptop**, use this to open the chrome profile:
    ```
    CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'
    DRIVER_PATH = "C:\\Users\\pripuja\\Desktop\\Python\\chromedriver"

    # put this in the __init__ method
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    ```

- do not move/click anything on the selenium controlled browser
- make sure that any other chrome browser is closed otherwise it wont work
- please use the nili.thp.work gmail id to login to tradingview as the chart on that account has been set up in a specific way
- make sure that when the selenium controlled browser is opened, no other tab is manually opened