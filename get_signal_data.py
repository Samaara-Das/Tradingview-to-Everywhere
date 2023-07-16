'''
This module gets the entry signals from the premium screener on tradingview 
by getting data from alerts
'''

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# some constants
CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
DRIVER_PATH = 'C:\\Users\\Puja\\chromedriver'
EMAIL = 'dassamaara@gmail.com'
PWD = '1304sammy#'



class Browser:

  def __init__(self, driver: str, keep_open: bool) -> None:
    self.service = Service(driver)
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", keep_open)

    # make sure that any other chrome browser is closed otherwise it wont work
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=self.service, options=chrome_options)

  def open_page(self, url: str):
    self.driver.get(url)
    self.driver.maximize_window()
  
  def close_page(self):
    time.sleep(5)
    print("shutting down browser 💤")
    self.driver.close()

  def sign_in(self):
    # open the sign in page
    self.open_page("https://www.tradingview.com/#signin")

    # click sign in (google fills our email & pwd automatically so we can just immediately click on sign in)
    sign_in_btn = self.driver.find_element(By.CSS_SELECTOR, ".submitButton-LQwxK8Bm.button-D4RPB3ZC.size-large-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC.stretch-D4RPB3ZC")
    sign_in_btn.click()

  def read_alert(self, msg):
    # Split the text into lines
    lines = msg.split('\n')  
    print(msg)
    self.close_alert()

    # lists for sell, buy entries and closed entries
    sell_list = []
    buy_list = []
    closed_buy_list = []
    closed_sell_list = []

    # go thru each line to see which one is about a buy or sell or a closed trade
    for i, line in enumerate(lines):
      # break the line up
      parts = line.split('|')

      if 'Buy' in line:
        buy_list.append({'entry': parts[0], 'tp': parts[1], 'sl': parts[2], 'symbol': parts[3], 'timeframe': parts[4]})
      
      if 'Sell' in line:
        sell_list.append({'entry': parts[0], 'tp': parts[1], 'sl': parts[2], 'symbol': parts[3], 'timeframe': parts[4]})
      
      # if 'Closed Buy' in line and 'TP' in line:
      #   closed_sell_list.append({'entry': parts[0], 'symbol': parts[1], 'timeframe': parts[2]})

      # if 'Closed Buy' in line and 'TP' in line:
      #   closed_buy_list.append({'entry': parts[0], 'symbol': parts[1], 'timeframe': parts[2]})

    


  def click_products_tab(self):
    while True:
      try:
          # Wait for the interfering element to disappear
          WebDriverWait(self.driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".header-v4NPAtHi")))
          
          # Click on the "Products" tab
          product_tab = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Products")))
          product_tab.click()
          
          # break the loop if we click on the element
          break
      except Exception as e:
          print(f"⛔ Error: {str(e)}")

  def close_alert(self):
    ok_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".button-D4RPB3ZC.size-small-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC")))
    ok_button.click()

  def get_data_from_alert(self):
    # the code below only works when there is an alert setup in our account.
    # if there is no alert set up in the alerts tab, create one for the premium screener
    alert_msg = None

    while True:
      try:
        alert_msg = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.secondaryRow-QkiHQU0S")))
        print('🔔 recieved alert')
        self.read_alert(alert_msg.text)
        alert_msg = None
      except Exception as e:
        continue
      


browser = Browser(DRIVER_PATH, True)

# sign in to the browser
browser.sign_in()

# click on "Products" tab
browser.click_products_tab()

# wait for an alert to popup
browser.get_data_from_alert()


# 🎯 TO-DO
# classify the buys, sells and exits into dictionaries

# after getting the text from the alert, read it. figure out if its about an entry or an exit (use regex)
# after knowing if its an entry or exit, go to that chart & timeframe
