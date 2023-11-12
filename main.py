'''
this is the main module where we use all the other modules to perform tasks
'''

import open_tv
import get_alert_data

SETUPS_INDICATOR = 'Screener' # short title of the screener
DRAWER_INDICATOR = 'Trade' # short title of the indicator which plots the entries/exits
SCREENER_NAME = 'Premium Screener' # name of the screener
TIMEFRAME = '1m' # timeframe of the chart which the alerts should be set on

# initiate Browser
browser = open_tv.Browser(True, SETUPS_INDICATOR, SCREENER_NAME, DRAWER_INDICATOR)
# open tradingview charts for X amount of tabs
browser.setup_tv()

# change the symbol settings of the indicators in differnt symbols and setup alerts for those symbol
browser.set_bulk_alerts(10)

# wait for alerts and get data from them abt a new entry/exit
# and then go that new entry's/exit's chart & timeframe
# take a snapshot and send to twitter
alerts = get_alert_data.Alerts(browser.driver, browser)
alerts.read_and_parse()
