'''
This sets up tradingview, the alerts and does a few things for the indicators
'''

# import modules
from time import sleep, time
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
SYMBOL_INPUTS = 15 #number of symbol inputs in the screener

CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
# CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'


# class
class Browser:

  def __init__(self, keep_open: bool, screener_shorttitle: str, screener_name: str, drawer_shorttitle: str, drawer_name: str) -> None:
    chrome_options = Options() 
    chrome_options.add_experimental_option("detach", keep_open)
    chrome_options.add_argument('--profile-directory=Profile 2')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    self.open_chart = OpenChart(self.driver)
    self.screener_name = screener_name
    self.screener_shorttitle = screener_shorttitle
    self.drawer_name = drawer_name
    self.drawer_shorttitle = drawer_shorttitle

  def open_page(self, url: str):
    self.driver.get(url)
    self.driver.maximize_window()
  
  def close_page(self):
    print("shutting down tab 💤")
    self.driver.close()

  def setup_tv(self):
    '''Open Tradingview, change to Screener layout, delete alerts, change timeframe and make the screener visible'''
    # open tradingview
    self.open_page('https://www.tradingview.com/chart')

    # change to the screener layout (if we are on any other layout)
    self.change_layout()

    # open the alerts sidebar
    self.open_alerts_sidebar()

    # delete all alerts
    self.delete_alerts()

    # load the screener and the trade drawer indicator
    self.load_indicators([self.screener_name, self.drawer_name])

    # make the screener and the trade drawer indicator into attributes of this object
    indicators = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')
    for ind in indicators: 
      indicator = ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text
      if indicator == self.screener_shorttitle: # finding the screener indicator
        self.screener_indicator = ind
      if indicator == self.drawer_shorttitle: # finding the trade drawer indicator
        self.drawer_indicator = ind

    # set the timeframe to 1m so that when the alert for the screener is set up, an error won't happen.
    # 1min is not the timeframe that entries are happening on. The timeframe for the entry is in the screener.
    self.open_chart.change_tframe('1')

    # make the screener visible
    self.indicator_visibility(True, self.screener_shorttitle)

    # make the Trade Drawer indicator visible
    self.indicator_visibility(True, self.drawer_shorttitle)

    #give it some time 
    sleep(2) 

  def set_bulk_alerts(self, alert_number: int):
    '''
    this makes `number` alerts (if there aren't already). The symbols given must cover all the alerts. 
    '''
    all_symbols = list(symbol_categories.keys()) # get all the symbols
    main_list = [all_symbols[i:i + SYMBOL_INPUTS] for i in range(0, len(all_symbols), SYMBOL_INPUTS)] # list of lists. each sublist is a set of symbols

    for _ in range(alert_number):
      if not main_list:
        print('Loop has been broken')
        break  # No more sublists left

      symbols = main_list.pop(0)  # Get the first sublist
      if len(symbols) == SYMBOL_INPUTS:
        self.open_chart.change_symbol(symbols[0])  # change chart's symbol
        self.change_settings(symbols)  # input the symbols in the screener's inputs
        self.is_loaded(self.screener_shorttitle)  # wait for the screener indicator to fully load
        if self.set_alerts():  # if an alert has been made, wait for it to be loaded
          self.is_alert_loaded(symbols[0], 10)

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
    # find the settings
    while True:
      try:
        ActionChains(self.driver).move_to_element(self.screener_indicator).perform()
        ActionChains(self.driver).double_click(self.screener_indicator).perform()
        settings = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
        break
      except:
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

  def open_alerts_sidebar(self):
    '''opens the alerts sidebar if it is closed. If it is already open, it does nothing'''
    alert_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="right-toolbar"] button[aria-label="Alerts"]')))
    if alert_button.get_attribute('aria-pressed') == 'false':
      alert_button.click()

  def set_alerts(self):
    # check if the screener indicator has an error
    if not self.is_no_error(self.screener_shorttitle):
      print('screener indicator had an error. Could not set an alert for this tab. Trying to reupload indicator')
      self.reupload_indicator(self.screener_name)
      self.is_loaded(self.screener_shorttitle) # wait for the screener indicator to fully load
      if not self.is_no_error(self.screener_shorttitle): # if an error is still there
        return False

    # click on the + button
    plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
    plus_button.click()
       
    # wait for the popup to show, click the dropdown and choose the screener
    set_alerts_popup = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
    set_alerts_popup.find_element(By.CSS_SELECTOR, 'span[data-name="main-series-select"]').click()
  
    for el in self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'):
      if self.screener_shorttitle in el.text:
        el.click()
        break    

    # click on submit
    self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]').click()

    return True

  def is_alert_loaded(self, chart_symbol, secs):
    '''this waits for `secs` seconds to see if a new alert has been loaded in the ALerts sidebar'''
    end_time = time() + secs
    while time() < end_time:
      elements_list = self.driver.find_elements(By.CSS_SELECTOR, '.list-G90Hl2iS div[data-name="alert-item-ticker"]')
      alert_symbols = [el.text for el in elements_list]
      if chart_symbol in alert_symbols:
        return True
    
    return False

  def is_loaded(self, ind_name):
    sleep(1)
    # find the indicator
    indicator = None
    if ind_name == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif ind_name == self.drawer_shorttitle:
      indicator = self.drawer_indicator

    # check if the indicator is not loading anymore
    while True:
      try:
        if 'loading' != indicator.get_attribute('data-status'): 
          break   
      except Exception as e:
        print(f'error in {__file__}: \n{e}')
        continue

  def indicator_visibility(self, make_visible: bool, name: str):
    # click on the indicator
    indicator = None
    indicator_path = 'div[data-name="legend-source-item"]'
    if name == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif name == self.drawer_shorttitle:
      indicator = self.drawer_indicator

    if indicator != None: # that means that we've found our indicator
      eye = indicator.find_element(By.CSS_SELECTOR, 'div[data-name="legend-show-hide-action"]')
      status = eye.get_attribute('title')
      
      if (make_visible == False and status == 'Hide') or (make_visible == True and status == 'Show'): 
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, indicator_path)))
        indicator.click()
        eye.click()

  def is_no_error(self, ind_name:str):
    '''
    this checks if the indicator has successfully loaded without an error
    '''
    # find the indicator
    indicator = None
    if ind_name == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif ind_name == self.drawer_shorttitle:
      indicator = self.drawer_indicator

    # if there is no error
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

  def close_tabs(self):
    current_window_handle = self.driver.current_window_handle
    window_handles = self.driver.window_handles

    # Close the remaining tabs
    for handle in window_handles:
      if handle != current_window_handle:
        self.driver.switch_to.window(handle)
        # try 3 times to close the tab
        for _ in range(3):
          try:
            self.driver.close()
            break
          except Exception as e:
            print(f'error in {__file__}... can\'t close tab \n{e}')


    # switch back to the first tab
    self.driver.switch_to.window(self.driver.window_handles[0])

  def reupload_indicator(self, ind_name: str):
    try:
      # click on screener indicator
      self.screener_indicator.click()

      # click on data-name="legend-delete-action" (a sub element under screener indicator)
      delete_action = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-delete-action"]')))
      delete_action.click()

      # click on indicators
      indicators_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[id="header-toolbar-indicators"] button[data-name="open-indicators-dialog"]')))
      indicators_button.click()

      # enter ind_name into search.
      search_input = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-role="search"]')))
      search_input.send_keys(ind_name)

      # find div[data-title] which is equal to ind_name and click on it (to upload the indicator)
      for element in WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-title]'))):
        if element.get_attribute('data-title') == ind_name:
            element.click()
            close_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-name="close"]')))
            close_button.click()
            break
    except Exception as e:
      print(f"An error occurred: {e}")

  def load_indicators(self, ind_names):
    indicators = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')
    for ind in indicators: # remove all the indicators on the chart
      ind.click()
      ind.find_element(By.CSS_SELECTOR, 'div[data-name="legend-delete-action"]').click()

    self.driver.find_element(By.CSS_SELECTOR, 'div[id="header-toolbar-indicators"] button[data-name="open-indicators-dialog"]').click()

    # load the indicators
    for i in range(2):
      # enter ind_name into search. 
      search_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-role="search"]')))
      search_input.send_keys(ind_names[i])

      # find div[data-title] which is ind_names[i] to ind_name and click on it (to upload the indicator)
      for element in self.driver.find_elements(By.CSS_SELECTOR, 'div[data-title]'):
        if element.get_attribute('data-title') == ind_names[i]:
          element.click()
          self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="close"]').click()
          break