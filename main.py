'''
this is the main module where we use all the other modules to perform tasks
'''

import open_tv
import get_alert_data

SCREENER_SHORT = 'Screener' # short title of the screener
DRAWER_SHORT = 'Trade' # short title of the trade drawer indicator 
SCREENER_NAME = 'Premium Screener' # name of the screener
DRAWER_NAME = 'Trade Drawer' # name of the trade drawer

# initiate Browser
browser = open_tv.Browser(True, SCREENER_SHORT, SCREENER_NAME, DRAWER_SHORT, DRAWER_NAME)
# setup the indicators, alerts etc.
browser.setup_tv()
# change the symbol settings of the indicators in differnt symbols and setup alerts for those symbol
browser.set_bulk_alerts(15)

# wait for alerts and get data about new entries/exits
alerts = get_alert_data.Alerts(browser.drawer_indicator, browser.driver, browser)
alerts.read_and_parse()
