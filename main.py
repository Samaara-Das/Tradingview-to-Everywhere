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

# testing to see if the indicator gets re uploaded
browser.reupload_indicator()
browser.screener_indicator = browser.get_indicator(browser.screener_shorttitle)
print('Screener indicator: ', browser.screener_indicator.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text)

# This method takes care of filling in the symbols, setting an alert and taking snaphots of the entries in those alerts and sending those to poolsifi and discord
# browser.post_everywhere()
