'''
This sets up tradingview, the alerts and does a few things for the indicators
'''

# import modules
import get_alert_data
from traceback import print_exc
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
from selenium.common.exceptions import WebDriverException

# some constants
SYMBOL_INPUTS = 15 #number of symbol inputs in the screener
CHART_TIMEFRAME = '1 hour' # the timeframe that the indicators will run on (not the timeframe that the entries will be on)
SCREENER_TIMEFRAME = '1 hour' # the timeframe that the screener will run on (the timeframe of the trades)
USED_SYMBOLS_INPUT = "Used Symbols" # Name of the Used Symbols input in the Screener
LAYOUT_NAME = 'Screener' # Name of the layout for the screener
SCREENER_MSG_TIMEOUT = 77 # seconds to wait for the screener message to appear in the Alerts log
SYMBOL_DELAY = 3 # seconds to wait for a new symbol to load 
SCREENER_REUPLOAD_TIMEOUT = 15 # seconds to wait for the screener to show up on the chart after re-uploading it
DEFAULT_SYMBOL = 'BTCUSD' # symbol which the chart will have (for the hour tracker alert to come within a minute..Other symbols might be closed)

CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
# CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'


# class
class Browser:

  def __init__(self, keep_open: bool, screener_shorttitle: str, screener_name: str, drawer_shorttitle: str, drawer_name: str, hour_tracker_name: str) -> None:
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
    self.hour_tracker_name = hour_tracker_name
    # Call the function to fill up symbol_set in symbol_settings.py
    fill_symbol_set(SYMBOL_INPUTS)

  def open_page(self, url: str):
    try:
      self.driver.get(url)
      self.driver.maximize_window()
      return True
    except WebDriverException:
      print(f'🔴 Cannot open this url: {url}. Error: ')
      print_exc()
      return False 

  def setup_tv(self):
    '''Open Tradingview, change to Screener layout, open the Alerts sidebar, delete all alerts, change timeframe to 1m and make both indicators visible'''
    # open tradingview
    if not self.open_page('https://www.tradingview.com/chart'):
      if not self.open_page('https://www.tradingview.com/chart'): # try once more
        print(f'🔴 Failed to open tradingview. Exiting function')
        return False

    # change to the screener layout (if we are on any other layout)
    if not self.change_layout():
      self.change_layout() # try once more
      if self.current_layout() != LAYOUT_NAME:
        print(f'🔴 Cannot change the layout to {LAYOUT_NAME}. Exiting function')
        return False

    # change the symbol to a crypto one so that the hour tracker alert can come within a minute (Other symbols might be closed)
    if not self.open_chart.change_symbol(DEFAULT_SYMBOL):
      self.open_chart.change_symbol(DEFAULT_SYMBOL) # try once more
      if not self.current_symbol() == DEFAULT_SYMBOL:
        print(f'🔴 Cannot change the symbol to {DEFAULT_SYMBOL}. Exiting function')
        return False

    # set the timeframe to 1H (so that the alert can come once every hour)
    if not self.open_chart.change_tframe(CHART_TIMEFRAME):
      self.open_chart.change_tframe(CHART_TIMEFRAME) # try once more
      if not self.current_chart_tframe() == CHART_TIMEFRAME:
        print(f'🔴 Cannot change the timeframe to {CHART_TIMEFRAME}. Exiting function')
        return False

    # open the alerts sidebar
    if not self.open_alerts_sidebar():
      self.open_alerts_sidebar() # try once more
      if not self.alerts_sidebar_open():
        print(f'🔴 Cannot open the alerts sidebar. Exiting function')
        return False

    # delete all alerts
    if not self.delete_all_alerts():
      self.delete_all_alerts() # try once more
      if not self.no_alerts():
        print(f'🔴 Cannot delete all alerts. Exiting function')
        return False

    # make the screener and the trade drawer indicator into attributes of this object
    self.screener_indicator = self.get_indicator(self.screener_shorttitle)
    self.drawer_indicator = self.get_indicator(self.drawer_shorttitle)
    self.hour_tracker_indicator = self.get_indicator(self.hour_tracker_name)

    if self.screener_indicator is None: # try once more to find the screener
      self.screener_indicator = self.get_indicator(self.screener_shorttitle)

    if self.drawer_indicator is None: # try once more to find the trade drawer
      self.drawer_indicator = self.get_indicator(self.drawer_shorttitle)

    if self.hour_tracker_indicator is None: # try once more to find the hour tracker
      self.hour_tracker_indicator = self.get_indicator(self.hour_tracker_name)

    if self.screener_indicator is None or self.drawer_indicator is None or self.hour_tracker_indicator is None:
      print(f'🔴 One of the indicators is not found. Exiting function. Screener: {self.screener_indicator}, Trade Drawer: {self.drawer_indicator}, Hour Tracker: {self.hour_tracker_indicator}')
      return False

    self.alerts = get_alert_data.Alerts(self.drawer_indicator, self.screener_shorttitle, self.driver, self.hour_tracker_name, CHART_TIMEFRAME, SCREENER_TIMEFRAME, SCREENER_MSG_TIMEOUT)

    # make the screener visible, Trade Drawer indicator visible and Hour tracker invisible
    if not self.indicator_visibility(True, self.screener_shorttitle):
      self.indicator_visibility(True, self.screener_shorttitle)
      if self.is_visible(self.screener_shorttitle) == False:
        print('Failed to make the screener indicator visible. The function will still continue on without exiting as this is not crucial.')

    if not self.indicator_visibility(True, self.drawer_shorttitle):
      self.indicator_visibility(True, self.drawer_shorttitle)
      if self.is_visible(self.drawer_shorttitle) == False:
        print('Failed to make the Trade Drawer indicator visible. The function will still continue on without exiting as this is not crucial.')

    if not self.indicator_visibility(False, self.hour_tracker_name):
      self.indicator_visibility(False, self.hour_tracker_name)
      if self.is_visible(self.hour_tracker_name) == True:
        print('Failed to make the Hour tracker indicator invisible. The function will still continue on without exiting as this is not crucial.')

    # change the Timeframe input in the screener
    if not self.change_screener_timeframe(SCREENER_TIMEFRAME):
      self.change_screener_timeframe(SCREENER_TIMEFRAME)
      if not self.check_screener_timeframe(SCREENER_TIMEFRAME):
        print('🔴 Failed to change the Timeframe input in the screener. Exiting function.')
        return False

    #give it some time to rest
    sleep(2) 

    return True

  def post_everywhere(self):
    '''
    This method takes care of filling in the symbols, setting an alert and taking snaphots of the entries in those alerts and sending those to poolsifi and discord
    '''
    try:
      for category, symbols in symbol_set.items(): # This will go through each category's symbols
        for symbol_sublist in symbols: # this will go through each set of the current symbols
          chart_symbol = symbol_sublist[0] # the chart's symbol is the first symbol in the set
          if not self.open_chart.change_symbol(chart_symbol): # change chart's symbol
            print(f'Failed to change the chart\'s symbol to {chart_symbol}. Going to try with the next set of symbols for this category (if there are sets left)')
            continue
          if not self.is_market_open():
            print('Market is closed, on holiday or in its pre market hours. Skipping to next category.')
            break # if a us stock is closed, that means that other us stocks are also closed... So, skip to the next category
          if not self.change_settings(symbol_sublist): # input the symbols in the screener's inputs
            print('Failed to change screener\'s symbol settings. Going to try with the next set of symbols for this category (if there are sets left)')
            continue
          sleep(5) # wait for the screener indicator to fully load (we are avoiding to wait for the indicator to load as it will take too long)
          if not self.set_alerts(symbol_sublist): # wait for the screener to load and set an alert for it
            print('Failed to set alert for screener. Going to try with the next set of symbols for this category (if there are sets left)')
            continue
          if not self.is_alert_loaded(chart_symbol, 15): # if the alert has showed up
            print('Alert did not load. Going to try with the next set of symbols for this category (if there are sets left)')
            continue

          alert_msg = self.alerts.read_and_parse()
          self.alerts.post(alert_msg, self.indicator_visibility)
          self.indicator_visibility(True, self.screener_shorttitle) # making the screener visible if it has been hidden
          self.delete_all_alerts() # delete the alert for the screener so that we can start afresh
    except Exception as e:
      print('🔴 An error happened in post_everywhere. Error:')
      self.delete_all_alerts() # delete all alerts just in case this disn't happen before
      print_exc()
      return 
        
  def change_layout(self):
    try:
      # switch the layout if we are on some other layout. if we are on the screener layout, we don't need to do anything
      curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
      if curr_layout.find_element(By.CSS_SELECTOR, '.text-yyMUOAN9').text == LAYOUT_NAME:
        return True

      # click on the dropdown arrow
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/button[2]'))).click()
      
      # choose the screener layout
      layouts = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/a')))

      for layout in layouts:
        if layout.find_element(By.CSS_SELECTOR, '.layoutTitle-yyMUOAN9').text == LAYOUT_NAME:
          layout.click()
          return True
    except Exception as e:
      print('🔴 An error happened when changing the layout. Error:')
      print_exc()
      return False
    
  def current_layout(self):
    try:
      curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
      return curr_layout.find_element(By.CSS_SELECTOR, '.text-yyMUOAN9').text
    except Exception as e:
      print('🔴 An error happened when getting the current layout. Error:')
      print_exc()
      return ''

  def change_settings(self, symbols_list):
    try:
      # find the settings popup
      while True:
        try:
          # get the screener
          screener = self.get_indicator(self.screener_shorttitle)
          if not screener:
            print(f'🔴 Could not find screener indicator: {screener}. Exiting function.')
            return False
          
          # Open its settings
          self.screener_indicator = screener
          self.screener_indicator.click()
          WebDriverWait(self.screener_indicator, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-settings-action"]'))).click()
          settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
          break
        except WebDriverException as e:
          print('🔴 An exception happened when waiting for the settings to show up or for the ⚙️ button to be clickable.')
          if self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-settings-action"]'): # if the settings popup has opened up
            break
      
      symbol_inputs = settings.find_elements(By.CSS_SELECTOR, '.inlineRow-tBgV1m0B div[data-name="edit-button"]') # symbol inputs

      # fill in the Used Symbols input
      input_names = settings.find_elements(By.CSS_SELECTOR, 'div[class="cell-tBgV1m0B first-tBgV1m0B"] div[class="inner-tBgV1m0B"]')
      inputs = settings.find_elements(By.CSS_SELECTOR, 'div[class="cell-tBgV1m0B"] div[class="inner-tBgV1m0B"] > span')
      symbols_used_input = None

      for index, element in enumerate(input_names):
        if element.text == USED_SYMBOLS_INPUT:
          symbols_used_input = inputs[index]
          break

      symbols_used_input.send_keys(len(symbols_list))
      symbols_used_input.send_keys(Keys.ENTER)

      # change the symbol inputs based on the total number of symbols
      for i, to_be_symbol in enumerate(symbols_list):
        symbol_inputs[i].click()
        search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input')
        search_input.send_keys(to_be_symbol)
        search_input.send_keys(Keys.ENTER)

      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
      print('Successfully changed the inputs of the screener!')
      return True
    except Exception as e:
      print('🔴 Error ocurred when filling in the inputs of the screener. Error:')
      print_exc()
      return False

  def open_alerts_sidebar(self):
    '''opens the alerts sidebar if it is closed. If it is already open, it does nothing'''
    try:
      alert_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="right-toolbar"] button[aria-label="Alerts"]')))
      if alert_button.get_attribute('aria-pressed') == 'false':
        alert_button.click()
        return True
      else: # if the alerts sidebar is already open
        return True
    except Exception as e:
      print('🔴 An error happened when opening the alerts sidebar. Error:')
      print_exc()
      return False

  def set_alerts(self, symbols):
    # check if the screener indicator has an error
    if not self.is_no_error(self.screener_shorttitle):
      print('🔴 Screener indicator had an error. Could not set an alert for this tab. Trying to reupload indicator')
      if not self.reupload_indicator():
        print('🔴 Could not re-upload screener. Cannot set an alert for the screener. Exiting function.')
        return False
      if not self.change_settings(symbols):
        print('🔴 Could not input the symbols into the screener. Cannot set an alert for the screener. Exiting function.')
        return False
      sleep(5) # wait for the screener indicator to fully load (we are avoiding to wait for the indicator to load because it will take too long)
      if not self.is_no_error(self.screener_shorttitle): # if an error is still there
        print('🔴 Error is still there in the screener. Cannot set an alert for the screener. Exiting function.')
        return False
   
    # If no errors are there, try to set the alert for the screener
    try:
      # click on the + button
      plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
      plus_button.click()
        
      # wait for the create alert popup to show and click the dropdown 
      popup = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-name="main-series-select"]'))).click()
    
      # choose the screener
      screener_found = False
      for el in self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'):
        if self.screener_shorttitle in el.text:
          screener_found = True
          el.click()
          break    

      if not screener_found: # if the screener is not found, close the "Create Alert" popup and exit
        print('🔴 Failed to create alert. Screener is unavailable in the dropdown. Closing "Create Alert" popup. Exiting function.')
        popup.find_element(By.CSS_SELECTOR, 'button[data-name="close"]').click()
        return False
      
      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]').click()
      return True
    except Exception as e:
      print('🔴 Error occurred when setting up alert. Exiting function. Error:')
      print_exc()
      return False
  
  def set_hour_tracker_alert(self):
    try:
      # click on the + button
      plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
      plus_button.click()
          
      # wait for the popup to show, click the dropdown and choose Hour tracker
      WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-name="main-series-select"]'))).click()

      for el in self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'):
        if self.hour_tracker_name in el.text:
          el.click()
          break    

      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]').click()
      return True
    except Exception as e:
      print('🔴 Error occurred when setting the hour tracker alert. Error:')
      print_exc()
      return False

  def is_alert_loaded(self, chart_symbol, secs):
    '''this waits for `secs` seconds to see if a new alert has been loaded in the Alerts sidebar'''
    end_time = time() + secs
    val = False
    try:
      while time() < end_time:
        elements_list = self.driver.find_elements(By.CSS_SELECTOR, '.list-G90Hl2iS span[data-name="alert-item-ticker"]')
        alert_symbols = [el.text for el in elements_list]
      
        if any(chart_symbol in symbol for symbol in alert_symbols):
            val = True
            print('Alert for the screener has successfully loaded in the Alerts sidebar!')
            sleep(1)
            break
    except Exception as e:
      print('🔴 Error occurred when checking if the alert for the screener has loaded. Error:')
      print_exc()

    return val

  def is_indicator_loaded(self, shorttitle):
    sleep(1)
    # find the indicator
    indicator = None
    if shorttitle == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif shorttitle == self.drawer_shorttitle:
      indicator = self.drawer_indicator

    # check if the indicator is not loading anymore
    while True:
      try:
        if 'loading' != indicator.get_attribute('data-status'): 
          break   
      except Exception as e:
        print_exc()
        continue

  def indicator_visibility(self, make_visible: bool, shorttitle: str):
    '''Makes `shorttitle` indicator visible or hidden'''

    # get the indicator
    indicator = None
    if shorttitle == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif shorttitle == self.drawer_shorttitle:
      indicator = self.drawer_indicator
    elif shorttitle == self.hour_tracker_name:
      indicator = self.hour_tracker_indicator

    try:
      if indicator != None: # that means that we've found our indicator
        eye = indicator.find_element(By.CSS_SELECTOR, 'div[data-name="legend-show-hide-action"]')
        status = 'Hidden' if 'disabled' in indicator.get_attribute('class') else 'Shown'
        
        if make_visible == False: 
          if status == 'Shown': # if status is "Hidden", that means that it is already hidden
            indicator.click()
            eye.click()
            return True

        if make_visible == True: 
          if status == 'Hidden': # if status is "Shown", that means that it is already shown
            indicator.click()
            eye.click()
            return True
    except Exception as e:
      print(f'🔴 Error ocurred when changing the visibility of {shorttitle} to make it {"visible" if make_visible else "invisible"}. Error:')
      print_exc()
      return False
    
    return False

  def is_visible(self, shorttitle: str):
    '''This returns `True` if the visibility of `shorttitle` indicator is shown. Otherwise, this returns `False` if its visibility is hidden.'''
    # get the indicator
    indicator = None
    if shorttitle == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif shorttitle == self.drawer_shorttitle:
      indicator = self.drawer_indicator
    elif shorttitle == self.hour_tracker_name:
      indicator = self.hour_tracker_indicator
      
    # check its visibility
    try:
      if indicator != None: # that means that we've found our indicator
        status = 'Hidden' if 'disabled' in indicator.get_attribute('class') else 'Shown'
        return status == 'Shown'
    except Exception as e:
      print(f'🔴 Error ocurred when checking the visibility of {shorttitle} indicator. Error:')
      print_exc()
      return False
    
    return False

  def is_no_error(self, shorttitle:str):
    '''
    this checks if the indicator has successfully loaded without an error
    '''
    try:
      # find the indicator
      indicator = None
      if shorttitle == self.screener_shorttitle:
        indicator = self.screener_indicator
      elif shorttitle == self.drawer_shorttitle:
        indicator = self.drawer_indicator

      # if there is no error
      if indicator.find_elements(By.CSS_SELECTOR, '.statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS') == []:
        print(f'There is no error in {shorttitle}!')
        return True
      
      print(f'There is an error in {shorttitle}.')
      return False
    except Exception as e:
      print(f'🔴 Error ocurred when checking if {shorttitle} had an error. Error:')
      print_exc()
      return False
    
  def delete_all_alerts(self):
    '''Waits for the alert sidebar to open up and deletes all the alerts if there are any.'''
    try:
      # wait for the alert sidebar to show up
      alert_sidebar1 = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.body-i8Od6xAB')))
      if not alert_sidebar1:
        print('🔴 Alert sidebar not found. Cannot delete all alerts.')
        return False

      # Check if there already are no alerts
      if self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div[class="itemBody-ucBqatk5 active-Bj96_lIl"]') == []:
        print('There are no active alerts. No need to delete any alerts!')
        return True

      # click the 3 dots
      settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]')))
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))).click()
         
      # delete all alerts
      WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')))[-1].click() # in the dropdown which it opens, choose the "Remove all" option
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="yes"]'))).click() # click OK when the confirm dialog pops up

      sleep(1)
      if len(self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5')) == 0: # if there are no alerts visible (that means that the alerts have been deleted)
        print('All alerts have been sucessfully deleted!')
        return True
    except Exception as e:
      print('🔴 Error happened somewhere when deleting all alerts. Failed to delete all alerts. Error:')
      print_exc()
      return False
    
    return False

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
            print(f'can\'t close tab')
            print_exc()

    # switch back to the first tab
    self.driver.switch_to.window(self.driver.window_handles[0])

  def reupload_indicator(self):
    '''removes screener and reuploads it again to the chart. It then waits for the screener to show up on the chart and returns `True` if it does otherwise `False`.

    Don't remove the print statements. It seems like the code will only run with the print statements.'''
    val = False

    try:
      # click on screener indicator
      self.screener_indicator.click()

      # click on data-name="legend-delete-action" (a sub element under screener indicator)
      delete_action = WebDriverWait(self.screener_indicator, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-delete-action"]')))
      print('Found remove button: ', delete_action)
      delete_action.click()

      # click on "Favorites" dropdowm
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[id="header-toolbar-indicators"] button[data-name="show-favorite-indicators"]'))).click()
      print('favorites dropdown was clicked')

      # Wait for the dropdown menu to appear
      menu = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]')))
      print('dropdown menu appeared')

      # find Premium Screener in the dropdown menu and click on it
      dropdown_indicators = WebDriverWait(menu, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-role="menuitem"]')))
      for el in dropdown_indicators:
        print('current indicator: ',el)
        text = el.find_element(By.CSS_SELECTOR, 'span[class="label-l0nf43ai apply-overflow-tooltip"]').text
        if self.screener_name == text:
          print('Found Premium Screener')
          if el.is_displayed():
            el.click()
            break
          else:
            # Scroll the element into view
            actions = ActionChains(menu).move_to_element(el)
            actions.perform()
            el.click()
            break
      
      # Wait for the indicator to show up on the chart
      start_time = time()
      timeout = SCREENER_REUPLOAD_TIMEOUT  # max seconds to wait
      while time() - start_time <= timeout:
        indicators = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')
        for ind in indicators:
          if ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text == self.screener_shorttitle:
            val = True
            break
        if val: # if the indicator is found on the chart, break the while loop
          print('The screener is on the chart after re-uploading it!')
          break
    except Exception as e:
      print('🔴 An error ocurred when re-uploading the screener. Could not reupload screener. Error: ')
      print_exc()
      return False

    return val

  def get_indicator(self, ind_shorttitle: str):
    '''Returns the indicator which has the given short title'''
    try:
      indicator = None
      wait = WebDriverWait(self.driver, 15)
      indicators = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')))
      
      for ind in indicators: 
        indicator_name = ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text
        if indicator_name == ind_shorttitle: # finding the indicator
          print(f'Found indicator {ind_shorttitle}!')
          indicator = ind
          break
    except Exception as e:
      print(f'🔴 Failed to find indicator {ind_shorttitle}. Error: ')
      print_exc()
      return None

    return indicator
    
  def change_screener_timeframe(self, tf: str):
    '''Changes the Timeframe input of the Screener indicator'''
    try:
      # open the settings of the screener
      self.screener_indicator.click()
      WebDriverWait(self.screener_indicator, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-settings-action"]'))).click()
      indicator_popup = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-dialog-name="Screener"]')))
      settings = indicator_popup.find_element(By.CSS_SELECTOR, '.content-tBgV1m0B')
       
      # click on the Timeframe input
      tf_input = settings.find_element(By.CSS_SELECTOR, 'div[class="cell-tBgV1m0B"] span[data-role="listbox"]')
      tf_input.click()

      # select the desired timeframe from the dropdown
      dropdown = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]')))
      timeframes = dropdown.find_elements(By.CSS_SELECTOR, 'div[role="option"]')
      for timeframe in timeframes:
        if timeframe.find_element(By.CSS_SELECTOR, 'span[class="label-jFqVJoPk"]').text == tf:
          timeframe.click()
          break

      # click the Ok button
      indicator_popup.find_element(By.CSS_SELECTOR, 'button[data-name="submit-button"]').click()
      print(f'Timeframe of the screener successfully changed to {tf}!')
      return True
    except Exception as e:
      print(f'🔴 Failed to change Timeframe of the screener to {tf}. Error: ')
      print_exc()
      return False
    
  def check_screener_timeframe(self, tf: str):
    '''Checks if the Timeframe input of the Screener indicator is the same as `tf`. Returns `True` if it is the same, `False` otherwise.'''
   try:
      # open the settings of the screener
      self.screener_indicator.click()
      WebDriverWait(self.screener_indicator, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-settings-action"]'))).click()
      indicator_popup = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-dialog-name="Screener"]')))
      settings = indicator_popup.find_element(By.CSS_SELECTOR, '.content-tBgV1m0B')
       
      # Get the current value of the Timeframe input
      tf_val = settings.find_element(By.CSS_SELECTOR, 'div[class="cell-tBgV1m0B"] span[data-role="listbox"] span[class="button-children-tFul0OhX"] span').text
      return tf_val == tf
    except Exception as e:
      print(f'🔴 Failed to check the timeframe of the screener. Error: ')
      print_exc()
      return False

  def is_market_open(self):
    '''This waits for `symbol` to be loaded on the chart and waits for a few seconds (to give the chart time to load). Then, it checks if the market is open'''

    # The elements below are here just in case we need them
    # market_open_status = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="statusItem-Lgtz1OtS small-Lgtz1OtS marketStatusOpen-Lgtz1OtS"]')))
    # market_post_status = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="statusItem-Lgtz1OtS small-Lgtz1OtS marketStatusPost-Lgtz1OtS"]')))

    try:
      sleep(SYMBOL_DELAY) # wait for the chart to load and then check if the market is open
      
      # if there is no market close/market holiday button, that means that the market is open
      market_close = self.driver.find_elements(By.CSS_SELECTOR, 'div[class="statusItem-Lgtz1OtS small-Lgtz1OtS marketStatusClose-Lgtz1OtS"]')
      market_holiday = self.driver.find_elements(By.CSS_SELECTOR, 'div[class="statusItem-Lgtz1OtS small-Lgtz1OtS marketStatusHoliday-Lgtz1OtS"]')
      market_pre_hours = self.driver.find_elements(By.CSS_SELECTOR, 'div[class="statusItem-Lgtz1OtS small-Lgtz1OtS marketStatusPre-Lgtz1OtS"]')
      if not market_close and not market_holiday and not market_pre_hours: # if there is no market close/market holiday/pre hours button, then the market is open
        print('The market is open!')
        return True
      else:
        print('The market is not open.')
        return False
    except Exception as e:
      print('🔴 An error occurred when checking if the market is open. Exiting function.')
      print_exc()
      return False
    
  def current_symbol(self):
    '''Returns the current symbol'''
    try:
      symbol_search = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-symbol-search"]')))
      return symbol_search.find_element(By.CSS_SELECTOR, 'div').text
    except Exception as e:
      print('🔴 Failed to get the current symbol. Error:')
      print_exc()
      return ''
    
  def current_chart_tframe(self):
    '''Returns the current chart timeframe'''
    try:
      tf_button = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))
      return tf_button.get_attribute('aria-label')
    except Exception as e:
      print('🔴 Failed to get the current chart timeframe. Error:')
      print_exc()
      return ''
    
  def alerts_sidebar_open(self):
    '''This checks if the Alerts sidebar is open'''
    try:
      alert_button = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="right-toolbar"] button[aria-label="Alerts"]')))
      if alert_button.get_attribute('aria-pressed') == 'true': # if the alerts sidebar is open
        alert_button.click()
        return True
    except Exception as e:
      print('🔴 Failed to check if the Alerts sidebar is open. Error:')
      print_exc()
      return False
    
  def no_alerts(self):
    '''This checks if there no alerts'''
    try:
      alerts = self.driver.find_elements(By.CSS_SELECTOR, '.list-G90Hl2iS div[class="itemBody-ucBqatk5 active-Bj96_lIl"]')
      if not alerts: # if there are no alerts
        return True
    except Exception as e:
      print('🔴 Failed to check if there are no alerts. Error:')
      print_exc()
      return False
