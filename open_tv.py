'''
This module opens tradingview, signs in and goes to the chart
'''

# import modules
import time
from symbol_settings import *
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
# CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'
# DRIVER_PATH = "C:\\Users\\pripuja\\Desktop\\Python\\chromedriver"

# EMAIL = 'dassamaara@gmail.com'
# PWD = '1304sammy#'
# this is the best email id for logging in because tradingview automatically logs in & doesn't ask for a captcha
# AND the tradingview chart on this email id has been set up in a specific way
EMAIL = 'nili.thp.work@gmail.com'
PWD = 'Das12345'


# class
class Browser:

  def __init__(self, driver: str, keep_open: bool) -> None:
    self.service = Service(driver)
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", keep_open)

    # make sure that any other chrome browser is closed otherwise it wont work
    # chrome_options.add_argument('--profile-directory=Profile 5')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=self.service, options=chrome_options)

  def open_page(self, url: str):
    self.driver.get(url)
    self.driver.maximize_window()
  
  def close_page(self):
    time.sleep(5)
    print("shutting down browser 💤")
    self.driver.close()

  def open_tv_tabs(self, extra_tabs: int = 2):
    # open the tradingview tabs
    self.open_page('https://www.tradingview.com/chart')
    for i in range(extra_tabs):
      self.driver.execute_script("window.open('https://www.tradingview.com/chart','_blank')")

  def change_settings(self):
    symbols_list = [forex_symbols, stock_symbols, crypto_symbols]

    for tab in range(3):
      # switch to each tab
      self.driver.switch_to.window(self.driver.window_handles[tab])
      
      # inside the tab, click on the settings of the 2nd indicator
      indicator = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')[1]

      ActionChains(self.driver).move_to_element(indicator).perform()
      ActionChains(self.driver).double_click(indicator).perform()

      while True:
        try:
          settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
          break
        except Exception as e:
          continue
      inputs = settings.find_elements(By.CSS_SELECTOR, '.inlineRow-D8g11qqA div[data-name="edit-button"]')
      
      # fill up the settings
      for i, symbol in enumerate(inputs):
        to_be_symbol = symbols_list[tab][i]
        symbol.click()
        search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input')
        search_input.send_keys(to_be_symbol)
        search_input.send_keys(Keys.ENTER)

      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
