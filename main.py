'''
this is the main module where we use all the other modules to perform tasks
'''

import open_tv
import get_alert_data

# initiate Browser
browser = open_tv.Browser(open_tv.DRIVER_PATH, True)

# open tradingview chart directly
browser.open_tv_chart()

# wait for alerts and get data from them abt a new entry/exit
# and then go that new entry's/exit's chart & timeframe
alerts = get_alert_data.Alerts(browser.driver)
alerts.get_data_from_alert()
