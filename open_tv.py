'''
This module opens tradingview, signs in and goes to the chart
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
    for i in range(3):
      # switch to each tab
      self.driver.switch_to.window(self.driver.window_handles[i])
      
      # inside the tab, click on the settings of the 2nd indicator
      indicator = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')[1]

      ActionChains(self.driver).move_to_element(indicator).perform()
      ActionChains(self.driver).double_click(indicator).perform()

      settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
      inputs = settings.find_elements(By.CSS_SELECTOR, '.cell-tBgV1m0B input')[:-1]
      time.sleep(5)
      

    # fill up the settings