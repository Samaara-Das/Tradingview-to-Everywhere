'''
this is the main module where we use all the other modules to perform tasks
'''

import open_tv
import get_alert_data

# how many alerts do we want to set up
ALERTS = 3

# initiate Browser
browser = open_tv.Browser(open_tv.DRIVER_PATH, True)

# open tradingview chart
browser.open_tv()

# change the symbol settings of the indicators in differnt symbols and setup alerts for those symbol
browser.set_alerts_and_settings(ALERTS)

# wait for alerts and get data from them abt a new entry/exit
# and then go that new entry's/exit's chart & timeframe
# take a snapshot and send to twitter
alerts = get_alert_data.Alerts(browser.driver)
alerts.send_to_twitter()
