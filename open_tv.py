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
CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
DRIVER_PATH = 'C:\\Users\\Puja\\chromedriver'
# CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'
# DRIVER_PATH = "C:\\Users\\pripuja\\Desktop\\Python\\chromedriver"

EMAIL = 'dassamaara@gmail.com'
PWD = '1304sammy#'

# class
class Browser:

  def __init__(self, driver: str, keep_open: bool, tabs: int) -> None:
    self.service = Service(driver)
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", keep_open)

    # make sure that any other chrome browser is closed otherwise it wont work
    chrome_options.add_argument('--profile-directory=Profile 2')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
    self.tabs = tabs

  def open_page(self, url: str):
    self.driver.get(url)
    self.driver.maximize_window()
  
  def close_page(self):
    print("shutting down tab 💤")
    self.driver.close()

  def open_tv(self):
    # open tradingview
    self.open_page('https://www.tradingview.com/chart')

    # delete all alerts
    self.delete_alerts()

    tabs = self.tabs-1
    for i in range(tabs):
      self.driver.execute_script("window.open('https://www.tradingview.com/chart','_blank')")

  def set_alerts_and_settings(self):
    '''
    param alerts must be less than/equal to the number of tuples in symbols_settings.py 
    '''
    symbols_list = [crypto_symbols, crypto_symbols2, crypto_symbols3] 

    for tab in range(self.tabs):
      # switch tab
      self.driver.switch_to.window(self.driver.window_handles[tab])

      # change settings this particular symbol
      self.change_settings(symbols_list[tab][0], symbols_list[tab])

      # setup alert for this particular symbol
      self.set_alerts(tab)

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
    inputs = settings.find_elements(By.CSS_SELECTOR, '.inlineRow-D8g11qqA div[data-name="edit-button"]')[:-2]
    
    # fill up the settings
    for i, _symbol in enumerate(inputs):
      to_be_symbol = symbols_list[i]
      _symbol.click()
      search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input')
      search_input.send_keys(to_be_symbol)
      search_input.send_keys(Keys.ENTER)

    # click on submit
    self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()

  def set_alerts(self, tab):
    tab_no = tab + 1

    while True:
      try:
        # wait for the + button to be clickable
        plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
        break
      except Exception as e:
        continue


    # wait for the set alerts popup box
    while True:
      try:
        # click on the + button
        plus_button.click()
        set_alerts_popup = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
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

    # wait untill this new alert has come up in the alerts tab (if the number of alerts are equal to the number of tabs we hv set )
    while True:
      if len(self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5')) == tab_no:
        break
      else:
        continue

  def is_eye_loaded(self):
    while True:
      try:
        indicator = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')[1]
        if indicator.get_attribute('class') == 'item-jFqVJoPk withIcon-jFqVJoPk withIcon-xZRtm41u':
          return True   
      except Exception as e:
        return False

  def delete_alerts(self):
    while True:
      # click the 3 dots
      while True:
        try:
          settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]')))
          settings.click()
          break
        except Exception as e:
          continue

      try:
        # in the dropdown which it opens, choose the "Remove all" option
        WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')))[-1].click()
        
        # click OK when the confirm dialog pops up
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="yes"]'))).click()
      except Exception as e:
        # the error will happen when there are no alerts and the "Remove all" option is not there
        print(f'error in {__file__}', e)

      if len(self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5')) == 0:
        break

  def close_tabs(self):
    current_window_handle = self.driver.current_window_handle
    window_handles = self.driver.window_handles

    # Close the remaining tabs
    for handle in window_handles:
      if handle != current_window_handle:
        self.driver.switch_to.window(handle)
        self.driver.close()

    # switch back to the first tab
    self.driver.switch_to.window(self.driver.window_handles[0])


