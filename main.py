'''
this is where the main stuff happens
'''

import open_tv
import get_alert_data
import open_entry_chart
from resources.symbol_settings import *

# some constants
TRADE_DRAWER = 'Trade' # short title of indicator which draws the trades
SETUP = 'Setup' # short title of indicator which finds setups
TIMEFRAME = '15'

# initiate Browser
tv = open_tv.Browser(True)

# open tradingview chart
tv.setup_tv()

# object for doing things for displaying the entries 
trade_drawer = open_entry_chart.OpenChart(tv.driver)

# instantiating alert data
alert = get_alert_data.Alerts(tv.driver, tv)

for symbol, category in list(symbol_categories.items())[:5]:
    # go through every symbol 
    tv.chart.change_symbol(symbol)

    # give it some time to load
    open_tv.sleep(2)

    # set up an alert after the ILK indicator has loaded
    tv.set_alerts()

    # wait for an alert to come and get its content
    data = alert.read_and_parse()
    if data == '':
        continue # if it is empty, skip to the next symbol

    direction = data['direction']
    entry_time = data['entryTime']
    entry_price = data['entryPrice']
    sl_price = data['slPrice']
    tp_price = data['tpPrice']

    # get the info of the alert and put that into trade drawer
    trade_drawer.change_indicator_settings(TRADE_DRAWER, entry_time, entry_price, sl_price, tp_price, data['tp2Price'], data['tp3Price'])
    
    # after it has loaded, open in new tab and get link of the tab
    img_url = trade_drawer.save_chart_img()

    # send that to Poolsifi and discord
    category = symbol_category(symbol)
    content = f"{direction} in {symbol} at {entry_price}, Takeprofit: {tp_price}, Stoploss: {sl_price} {{}}".format(img_url)
    alert.send_to_db(data['type'], data['direction'], symbol, data['timeframe'], entry_price, tp_price, sl_price, img_url, content, entry_time, category, '')

    # delete the alert after reading it
    tv.delete_alerts()

