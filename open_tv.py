'''
This module opens tradingview, signs in and goes to the chart
'''

# import modules
import time
from open_entry_chart import OpenChart
from symbol_settings import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


# some constants
# CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
# DRIVER_PATH = 'C:\\Users\\Puja\\chromedriver'
CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'
DRIVER_PATH = "C:\\Users\\pripuja\\Desktop\\Python\\chromedriver"

EMAIL = 'dassamaara@gmail.com'
PWD = '1304sammy#'
# this is the best email id for logging in because tradingview automatically logs in & doesn't ask for a captcha
# AND the tradingview chart on this email id has been set up in a specific way
# EMAIL = 'nili.thp.work@gmail.com'
# PWD = 'Das12345'


# class
class Browser:

  def __init__(self, driver: str, keep_open: bool) -> None:
    self.service = Service(driver)
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", keep_open)

    # make sure that any other chrome browser is closed otherwise it wont work
    chrome_options.add_argument('--profile-directory=Profile 1')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=self.service, options=chrome_options)

  def open_page(self, url: str):
    self.driver.get(url)
    self.driver.maximize_window()
  
  def close_page(self):
    time.sleep(5)
    print("shutting down browser 💤")
    self.driver.close()

  def open_tv(self):
    # open tradingview
    self.open_page('https://www.tradingview.com/chart')

  def set_alerts_and_settings(self, alerts):
    '''
    param alerts must be less than/equal to the number of tuples in symbols_settings.py 
    '''
    
    symbols_list = [forex_symbols, stock_symbols, crypto_symbols]

    for j in range(alerts):
      #change settings this particular symbol
      self.change_settings(symbols_list[j][0], symbols_list[j])

      # setup alert for this particular symbol
      self.set_alerts()


  def change_settings(self, symbol, symbols_list):
    '''
    param symbol is the symbol you want the chart to change to
    '''

    # change the symbol of the current chart
    OpenChart(self.driver).change_symbol(symbol)
    
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
    for i, _symbol in enumerate(inputs):
      to_be_symbol = symbols_list[i]
      _symbol.click()
      search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input')
      search_input.send_keys(to_be_symbol)
      search_input.send_keys(Keys.ENTER)

    # click on submit
    self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()

  def set_alerts(self):
    # click the + button
    self.driver.find_element(By.CSS_SELECTOR, 'div[data-name="set-alert-button"]').click()

    while True:
      try:
        # wait for the set alerts popup box
        set_alerts_popup = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
        break
      except Exception as e:
        continue

    # click the dropdown and choose the screener
    set_alerts_popup.find_element(By.CSS_SELECTOR, 'span[data-name="main-series-select"]').click()

    for el in self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'):
      if 'Screener' in el.text:
        el.click()
        break    

    # click on submit
    self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]').click()

