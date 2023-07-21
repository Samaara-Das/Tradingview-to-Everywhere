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
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=self.service, options=chrome_options)

  def open_page(self, url: str):
    self.driver.get(url)
    self.driver.maximize_window()
  
  def close_page(self):
    time.sleep(5)
    print("shutting down browser 💤")
    self.driver.close()

  def open_tv_chart(self):
    # open the tradingview chart 
    self.open_page("https://www.tradingview.com/chart")

  def sign_in(self):
    # open the sign in page
    self.open_page("https://www.tradingview.com/#signin")

    # click sign in (google fills our email & pwd automatically so we can just immediately click on sign in)
    try:
      sign_in_btn = self.driver.find_element(By.CSS_SELECTOR, ".submitButton-LQwxK8Bm.button-D4RPB3ZC.size-large-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC.stretch-D4RPB3ZC")
      sign_in_btn.click()
    except:
      print('⛔ Couldn\'t sign in')

  def click_products_tab(self):
    while True:
      try:
          # Wait for the interfering element to disappear
          # WebDriverWait(self.driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".header-v4NPAtHi")))
          
          # Click on the "Products" tab
          product_tab = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div[3]/div[2]/div[2]/nav/ul/li[1]")))
          product_tab.click()
          
          # break the loop if we click on the element
          break
      except Exception as e:
          print(f"⛔ Error: {str(e)}")



