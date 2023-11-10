'''
This sets up tradingview, the alerts and does a few things for the indicators
'''

# import modules
from time import sleep
from open_entry_chart import OpenChart
from resources.symbol_settings import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By



# some constants
TRADE_DRAWER = 'Trade' # short title of indicator which draws the trades
SETUP = 'Setup' # short title of indicator which finds setups

CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
# CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'


# class
class Browser:

  def __init__(self, keep_open: bool) -> None:
    chrome_options = Options() 
    chrome_options.add_experimental_option("detach", keep_open)

    chrome_options.add_argument('--profile-directory=Profile 2')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    self.chart = OpenChart(self.driver)

  def open_page(self, url: str):
    self.driver.get(url)
    self.driver.maximize_window()
  
  def close_page(self):
    print("shutting down tab 💤")
    self.driver.close()

  def setup_tv(self, tf):
    # open tradingview
    self.open_page('https://www.tradingview.com/chart')

    # change to the screener layout (if we are on any other layout)
    self.change_layout()

    # open the alerts sidebar
    self.open_alerts_sidebar()

    # delete all alerts
    self.delete_alerts()

    # set the timeframe
    self.chart.change_tframe(tf)

    # make the Ichimoku, LC, Kernel indicator invisible
    self.indicator_visibility(False, SETUP)

    # make the Trade Drawer indicator visible
    self.indicator_visibility(True, TRADE_DRAWER)

  def open_alerts_sidebar(self):
    '''opens the alerts sidebar if it is closed. If it is already open, it does nothing'''
    alert_button = self.driver.find_element(By.CSS_SELECTOR, 'div[data-name="right-toolbar"] button[aria-label="Alerts"]')
    if alert_button.get_attribute('aria-pressed') == 'false':
      alert_button.click()

  def change_layout(self):
    # switch the layout if we are on some other layout. if we are on the screener layout, we don't need to do anything
    curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
    if curr_layout.find_element(By.CSS_SELECTOR, '.text-yyMUOAN9').text == 'Screener':
      return

    # click on the dropdown arrow
    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/button[2]'))).click()
    
    # choose the screener layout
    layouts = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/a')))

    for layout in layouts:
      if layout.find_element(By.CSS_SELECTOR, '.layoutTitle-yyMUOAN9').text == 'Screener':
        layout.click()
        break

  def change_settings(self, symbols_list):
    '''
    param symbol is the symbol you want the chart to change to
    '''

    if not len(symbols_list) >= SYMBOL_INPUTS:
      print('there are not enough symbols to cover all the inputs. exiting method')
      return

    # change the symbol of the current chart
    self.chart.change_symbol(symbols_list[0])

    # inside the tab, click on the settings of the 2nd indicator
    indicator = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')))[1]

    while True:
      try:
        ActionChains(self.driver).move_to_element(indicator).perform()
        ActionChains(self.driver).double_click(indicator).perform()
        settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
        break
      except Exception as e:
        print(f'error in {__file__}: \n{e}')
        continue
    inputs = settings.find_elements(By.CSS_SELECTOR, '.inlineRow-tBgV1m0B div[data-name="edit-button"]')
    
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
    # click on the + button
    plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
    plus_button.click()
      
    # wait for the alert popup and click the dropdown 
    set_alerts_popup = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
    set_alerts_popup.find_element(By.CSS_SELECTOR, 'span[data-name="main-series-select"]').click() # this will cause an error if the element will not exist. It might not exist because the Setup indicator has an error
    
    # choose the setup indicator
    for el in self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'):
      if SETUP in el.text:
        el.click()
        break    

    # click on create
    self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]').click()

    # wait for the alert to load
    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alert-item-name"]')))

  def is_eye_loaded(self):
    sleep(1)
    while True:
      try:
        indicator = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')[1]
        if 'loading' not in indicator.get_attribute('class'):
          break   
      except Exception as e:
        print(f'error in {__file__}: \n{e}')
        continue

  def indicator_visibility(self, make_visible: bool, name: str):
    # click on the indicator
    indicator_path = 'div[data-name="legend-source-item"]'
    indicator = None
    indicators = self.driver.find_elements(By.CSS_SELECTOR, indicator_path)
    for ind in indicators:
      if ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text == name:
        indicator = ind
        break

    if indicator != None: # that means that we've found our indicator
      eye = indicator.find_element(By.CSS_SELECTOR, 'div[data-name="legend-show-hide-action"]')
      status = eye.get_attribute('title')
      
      if make_visible == False: # if we want to make it invisible
        if status == 'Hide': # if status == 'Show', that means that it's already invisible
          WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, indicator_path)))
          indicator.click()
          eye.click()
      else: # if we want to make it visible 
        if status == 'Show': # if status == 'Hide', that means that it's already visible
          WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, indicator_path)))
          indicator.click()
          eye.click()

  def is_indicator_loaded(self, check_signal_ind=True):
    '''
    this checks if the indicator has successfully loaded without an error
    '''

    indicators =  WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')))
    indicator = None

    if check_signal_ind:
      # get the 1st indicator i.e. the signal indicator
      indicator = indicators[0]
    else:
      # get the 2nd indicator i.e. the screener indicator
      indicator = indicators[1]

    # if there is no element which resembles an error
    if indicator.find_elements(By.CSS_SELECTOR, '.statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS') == []:
      return True
    
    return False
    
  def delete_alerts(self):
    while True:
      # wait for the alert tab to load
      while True:
        try:
          alert_tab = self.driver.find_element(By.CSS_SELECTOR, '.body-i8Od6xAB') or self.driver.find_element(By.CSS_SELECTOR, '.wrapper-G90Hl2iS')
          break
        except Exception as e:
          print(f'error in {__file__}: \n{e}')
          continue

      # click the 3 dots
      while True:
        try:
          settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]')))
          settings.click()
          break
        except Exception as e:
          print(f'error in {__file__}: \n{e}')
          continue

      try:
        # in the dropdown which it opens, choose the "Remove all" option
        WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')))[-1].click()
        
        # click OK when the confirm dialog pops up
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="yes"]'))).click()
      except Exception as e:
        # the error will happen when there are no alerts and the remove all option is not there
        print(f'from {__file__}: \ncan\'t delete alerts. \n{e}')

      # if there are no alerts visible, break
      sleep(1)
      if len(self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5')) == 0:
        break

