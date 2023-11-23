'''
this is the main module where we use all the other modules to perform tasks
'''

import open_tv
from selenium.webdriver.common.by import By
from open_tv import sleep

SCREENER_SHORT = 'Screener' # short title of the screener
DRAWER_SHORT = 'Trade' # short title of the trade drawer indicator 
SCREENER_NAME = 'Premium Screener' # name of the screener
DRAWER_NAME = 'Trade Drawer' # name of the trade drawer
HOUR_TRACKER_NAME = 'Hour tracker' # name of the hour tracker indicator

# initiate Browser
browser = open_tv.Browser(True, SCREENER_SHORT, SCREENER_NAME, DRAWER_SHORT, DRAWER_NAME, HOUR_TRACKER_NAME)

# setup the indicators, alerts etc.
browser.setup_tv()

while True:
    try:
        browser.set_hour_tracker_alert() # set up alert for Hour tracker
        hour_alert = browser.alerts.read_hour_tracker_alert() # wait for an hour tracker alert
        if hour_alert:
            browser.delete_alerts() # delete the hour tracker alert so that no alerts come from it and the code doesn't read its alert and tries to jsonify it
            browser.post_everywhere() # This method takes care of filling in the symbols, setting an alert and taking snaphots of the entries in those alerts and sending those to poolsifi and discord

        browser.open_chart.change_symbol('BTCUSD') # change the symbol to a crypto one so that the hour tracker alert can come within a minute (Other symbols might be closed)
        sleep(3) # wait for the new symbol to load
    except Exception as e:
        from traceback import print_exc
        print('Error in main loop:')
        print_exc()


