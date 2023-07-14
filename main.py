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
DRIVER_PATH = 'C:\\Users\\Puja\\chromedriver'
EMAIL = 'dassamaara@gmail.com'
PWD = '1304sammy#'



class Browser:



  def __init__(self, driver: str, keep_open: bool) -> None:
    self.service = Service(driver)
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", keep_open)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
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

    # click the email button
    button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.NAME, "Email")))
    button.click()

    # enter email, password & click sign in
    self.driver.find_element(By.ID, "id_username").send_keys(EMAIL)
    self.driver.find_element(By.ID, "id_password").send_keys(PWD)
    sign_in_btn = self.driver.find_element(By.CSS_SELECTOR, ".submitButton-LQwxK8Bm.button-D4RPB3ZC.size-large-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC.stretch-D4RPB3ZC")
    sign_in_btn.click()

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

  def click_tweet_image(self):
    # click the camera button on the top-right i.e "Take a snapshot"
    WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Take a snapshot'] > div#header-toolbar-screenshot"))).click()
    
    # click the "tweet image" button
    tweet_image = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="tweet-chart-image"]')))
    tweet_image.click()

  def sign_in_to_twitter(self):
    # use switch_to() to switch to the new window
    # https://stackoverflow.com/questions/10629815/how-to-switch-to-new-window-in-selenium-for-python
    pass

  def save_chart_img(self):
    ActionChains(self.driver).key_down(Keys.ALT).send_keys('s').perform()
    element = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Save image')))
    element.click() 


browser = Browser(DRIVER_PATH, True)

# sign in
browser.sign_in()

# click on "Products" tab
browser.click_products_tab()

# click on "Tweet Image" button
browser.click_tweet_image()