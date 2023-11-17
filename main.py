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

# initiate Browser
browser = open_tv.Browser(True, SCREENER_SHORT, SCREENER_NAME, DRAWER_SHORT, DRAWER_NAME)

# setup the indicators, alerts etc.
browser.setup_tv()

# This method takes care of filling in the symbols, setting an alert and taking snaphots of the entries in those alerts and sending those to poolsifi and discord
browser.post_everywhere()
