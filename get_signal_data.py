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

  def close_pinescript_panel(self):
    try:
      minimize_panel = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Hide panel"]')))
      minimize_panel.click()
    except Exception as e:
      print(f"⛔ Couldn't close panel: {str(e)}")

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

  def get_data_from_alert(self):
    # the code below only works when there is an alert setup in our account.
    # if there is no alert set up in the alerts tab, create one for the premium screener
    alert_wrapper = None

    while True:
      try:
        alert_wrapper = WebDriverWait(self.driver, 10).until(EC.alert_is_present())
        print(alert_wrapper.find_element(By.CSS_SELECTOR, "div.secondaryRow-QkiHQU0S").text)
        break
      except Exception as e:
        print(f"⛔ Error: {str(e)}")
        continue
      


browser = Browser(DRIVER_PATH, True)

# sign in to the browser
browser.sign_in()

# click on "Products" tab
browser.click_products_tab()

# close pinescript panel
browser.close_pinescript_panel()

# wait for an alert to popup
browser.get_data_from_alert()