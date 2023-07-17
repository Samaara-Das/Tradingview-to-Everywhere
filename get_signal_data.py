'''
This module gets the entry signals from the premium screener on tradingview 
by getting data from alerts
'''

# import modules
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
# EMAIL = 'dassamaara@gmail.com'
# PWD = '1304sammy#'
EMAIL = 'nili.thp.work@gmail.com'
PWD = 'Das12345'


# class
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
    try:
      sign_in_btn = self.driver.find_element(By.CSS_SELECTOR, ".submitButton-LQwxK8Bm.button-D4RPB3ZC.size-large-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC.stretch-D4RPB3ZC")
      sign_in_btn.click()
    except:
      print('⛔ Couldn\'t sign in')

  def read_alert(self, msg):
    buy_list = []
    sell_list = []
    closed_buy_list = []
    closed_sell_list = []

    lines = msg.split('\n')
    self.close_alert()

    print('📖  reading lines')

    for line in lines:
      parts = line.split('|')

      if 'Buy' in line:
        buy_list.append({'entry': parts[1], 'tp': parts[2], 'sl': parts[3], 'symbol': parts[4], 'timeframe': parts[5]})
        print(buy_list[len(buy_list)-1])

      if 'Sell' in line:
        sell_list.append({'entry': parts[1], 'tp': parts[2], 'sl': parts[3], 'symbol': parts[4], 'timeframe': parts[5]})
        print(sell_list[len(sell_list)-1])

      # if 'Closed Sell' in line and 'TP' in line: 
      #   closed_sell_list.append({'entry': parts[0], 'symbol': parts[1], 'timeframe': parts[2]})
      #   print(closed_sell_list[len(closed_sell_list)-1])

      # if 'Closed Buy' in line and 'TP' in line:
      #   closed_buy_list.append({'entry': parts[0], 'symbol': parts[1], 'timeframe': parts[2]})
      #   print(closed_buy_list[len(closed_buy_list)-1])


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

    while True:
      try:
        alert_msg = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.secondaryRow-QkiHQU0S")))
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
# 🟢 classify the buys, sells and exits into dictionaries

# 🟢 after getting the text from the alert, read it. figure out if its about an entry or an exit (use regex)

# 🟡 print out the classified entries and exits in their lists and dictionaries

# 🔴 after knowing if its an entry or exit, go to that chart & timeframe
