'''
the main things that this does is:
opens Tradingview, sets it up, sets alerts for all the symbols, changes the layout, changes the screener's settings, creates an alert for the screener, changes the visibility of the indicators, deletes all the alerts and re-uploads the screener on the chart.

There are a few other things this does that are related to all the things mentioned above.
'''

from resources.utils import Utils
import handle_alerts
import logger_setup
from env import PROFILE
from os import getenv
from time import sleep, time
from open_entry_chart import OpenChart
from resources.symbol_settings import *
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import read_version_from_cmd 
from webdriver_manager.core.os_manager import PATTERN
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException, StaleElementReferenceException

# Set up logger for this file
open_tv_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

# some constants
SYMBOL_INPUTS = 5 #number of symbol inputs in the screener
CHART_TIMEFRAME = '1 minute' # the timeframe that the entries are from
USED_SYMBOLS_INPUT = "Used Symbols" # Name of the Used Symbols input in the Screener
LAYOUT_NAME = 'PointCapital' # Name of the layout for the screener
SCREENER_REUPLOAD_TIMEOUT = 15 # seconds to wait for the screener to show up on the chart after re-uploading it

CHROME_PROFILES_PATH = getenv('CHROME_PROFILES_PATH')

# generator functions
def main_list_gen():
  '''A generator which yields the main list of each category. Eg: [['AAPL', 'TSLA'], ['KO', 'SHOP']] and [['EURUSD', 'XAUUSD'], ['USDJPY', 'GBPUSD']]'''
  for _, main_list in symbol_set.items():
    yield main_list

def symbol_sublist_gen():
  '''A generator which yields each sublist of the main list. Eg: ['USDJPY', 'EURUSD', 'XAUUSD']'''
  main_lists = main_list_gen()
  for main_list in main_lists:
    for sublist in main_list:
      yield sublist


# class
class Browser:

  def __init__(self, keep_open: bool, screener_shorttitle: str, screener_name: str, drawer_shorttitle: str, drawer_name: str, interval_minutes: int, start_fresh: bool, screener_ob_short: str, screener_ob_name: str, screener_nw_short: str, screener_nw_name: str, screener_sb_short: str, screener_sb_name: str) -> None:
    chrome_options = Options() 
    chrome_options.add_experimental_option("detach", keep_open)

    chrome_options.add_argument(f'--profile-directory={PROFILE}')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILES_PATH}/TTE")
    chrome_options.add_argument("--remote-debugging-port=9224") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    cmd = "powershell -command \"&{(Get-Item 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe').VersionInfo.ProductVersion}\""
    version = read_version_from_cmd(cmd, PATTERN["google-chrome"])
    service = ChromeDriverManager(driver_version=version).install()
    self.driver = webdriver.Chrome(service=ChromeService(service), options=chrome_options)

    self.open_chart = OpenChart(self.driver)
    self.utils = Utils()
    self.screener_name = screener_name
    self.screener_shorttitle = screener_shorttitle
    self.drawer_name = drawer_name
    self.drawer_shorttitle = drawer_shorttitle
    self.screener_ob_short = screener_ob_short
    self.screener_ob_name = screener_ob_name
    self.screener_nw_short = screener_nw_short
    self.screener_nw_name = screener_nw_name
    self.screener_sb_short = screener_sb_short
    self.screener_sb_name = screener_sb_name
    self.interval_seconds = interval_minutes * 60 # Convert the interval to seconds
    self.start_fresh = start_fresh
    self.init_succeeded = True
    self.tv_email = ''
    self.tv_password = ''
    if start_fresh: 
      if not fill_symbol_set(SYMBOL_INPUTS): # Call the function to fill up symbol_set in symbol_settings.py
        open_tv_logger.error('Cannot fill up the symbol set. Exiting function')
        self.init_succeeded = False

  def open_page(self, url: str):
    '''This opens `url` and maximizes the window'''
    try:
      self.driver.get(url)
      self.driver.maximize_window()
      return True
    except WebDriverException:
      open_tv_logger.exception(f'Cannot open this url: {url}. Error: ')
      return False 

  def sign_in(self):
    '''This signs in to TradingView if logged out'''
    self.driver.get('https://www.tradingview.com/accounts/signin/')
    self.driver.maximize_window()
    try:
      # If the products menu is found, the user is signed in
      WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-main-menu-root-track-id="products"]')))
      return True
    except TimeoutException: # If the products menu is not found, the user is not signed in
      open_tv_logger.warning("Products menu not found within 5 seconds. User might not be signed in.")
      tv_email = getenv('TRADINGVIEW_EMAIL')
      tv_password = getenv('TRADINGVIEW_PASSWORD')
      
      if not tv_email or not tv_password:
        open_tv_logger.error("TradingView credentials not found in environment variables.")
        return False
      
      # wait for the name="Email" button to be present and click it
      WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.NAME, "Email"))).click()

      # Wait for the email input field to be present  
      email_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.NAME, "id_username")))
      email_input.send_keys(tv_email)

      # Wait for the password input field to be present
      password_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.NAME, "id_password")))
      password_input.send_keys(tv_password)

      # Wait for the sign in button to be clickable
      sign_in_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-overflow-tooltip-text="Sign in"]')
      sign_in_button.click()

      # Wait for the products menu to appear, indicating successful sign-in
      try:
        WebDriverWait(self.driver, 7).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-main-menu-root-track-id="products"]')))
        open_tv_logger.info("Successfully signed in to TradingView")
        return True
      except TimeoutException:
        open_tv_logger.error("Failed to sign in to TradingView")
        return False

  def setup_tv(self): 
    '''This opens tradigview, changes the layout of the chart, saves the layout if `LAYOUT_NAME` == 'Screener', opens the alert sidebar, deletes all alerts, gets access to the screener & trade drawer indicators, makes them both visible and changes the timeframe of the screener'''

    # sign in to tradingview
    if not self.sign_in():
      open_tv_logger.error('Failed to sign in to TradingView. Exiting function')
      return False

    # open tradingview
    if not self.open_page('https://www.tradingview.com/chart'):
      if not self.open_page('https://www.tradingview.com/chart'): # try once more
        open_tv_logger.error('Failed to open tradingview. Exiting function')
        return False

    # change to the correct layout (if we are on any other layout)
    if not self.change_layout(LAYOUT_NAME):
      self.change_layout(LAYOUT_NAME) # try once more
      if self.current_layout() != LAYOUT_NAME:
        open_tv_logger.error(f'Cannot change the layout to {LAYOUT_NAME}. Exiting function')
        return False
      
    # save the layout
    if not self.save_layout():
      if not self.save_layout(): # try once more
        open_tv_logger.warning(f'Cannot save the current layout {LAYOUT_NAME}. Exiting function')
        return False

    # set the timeframe to the correct timeframe
    if not self.open_chart.change_tframe(CHART_TIMEFRAME):
      self.open_chart.change_tframe(CHART_TIMEFRAME) # try once more
      if not self.current_chart_tframe() == CHART_TIMEFRAME:
        open_tv_logger.error(f'Cannot change the chart timeframe to {CHART_TIMEFRAME}. Exiting function')
        return False

    # open the alerts sidebar
    if not self.open_alerts_sidebar():
      self.open_alerts_sidebar() # try once more
      if not self.is_alerts_sidebar_open():
        open_tv_logger.error('Cannot open the alerts sidebar. Exiting function')
        return False

    # delete all alerts
    if self.start_fresh:
      if not self.delete_all_alerts():
        self.delete_all_alerts() # try once more
        if not self.no_alerts():
          open_tv_logger.error('Cannot delete all alerts. Exiting function')
          return False

    # verify that all required indicators are present on the chart
    screener_ob_check = self.get_indicator(self.screener_ob_short)
    screener_nw_check = self.get_indicator(self.screener_nw_short)
    screener_sb_check = self.get_indicator(self.screener_sb_short)
    drawer_check = self.get_indicator(self.drawer_shorttitle)

    if screener_ob_check is None: # try once more to find the Order Block screener
      screener_ob_check = self.get_indicator(self.screener_ob_short)

    if screener_nw_check is None: # try once more to find the Nadaraya Watson screener
      screener_nw_check = self.get_indicator(self.screener_nw_short)

    if screener_sb_check is None: # try once more to find the Structure break screener
      screener_sb_check = self.get_indicator(self.screener_sb_short)

    if drawer_check is None: # try once more to find the trade drawer
      drawer_check = self.get_indicator(self.drawer_shorttitle)

    if (screener_ob_check is None or screener_nw_check is None or 
        screener_sb_check is None or drawer_check is None):
      open_tv_logger.error(f'One or more indicators not found. Exiting function. Order Block: {screener_ob_check}, Nadaraya Watson: {screener_nw_check}, Structure break: {screener_sb_check}, Trade Drawer: {drawer_check}')
      return False

    self.alerts = handle_alerts.Alerts(self.drawer_shorttitle, [self.screener_ob_short, self.screener_nw_short, self.screener_sb_short], self.driver, CHART_TIMEFRAME, self.interval_seconds)

    # make the Trade Drawer indicator visible
    if not self.indicator_visibility(True, self.drawer_shorttitle):
      self.indicator_visibility(True, self.drawer_shorttitle)
      if self.is_visible(self.drawer_shorttitle) == False:
        open_tv_logger.warning('Failed to make the Trade Drawer indicator visible. The function will still continue on without exiting as this is not crucial.')
    
    # hide all 3 screener indicators
    if not self.indicator_visibility(False, self.screener_ob_short):
      self.indicator_visibility(False, self.screener_ob_short)
      if self.is_visible(self.screener_ob_short) == True:
        open_tv_logger.warning('Failed to hide the Order Block screener indicator. The function will still continue on without exiting as this is not crucial.')

    if not self.indicator_visibility(False, self.screener_nw_short):
      self.indicator_visibility(False, self.screener_nw_short)
      if self.is_visible(self.screener_nw_short) == True:
        open_tv_logger.warning('Failed to hide the Nadaraya Watson screener indicator. The function will still continue on without exiting as this is not crucial.')

    if not self.indicator_visibility(False, self.screener_sb_short):
      self.indicator_visibility(False, self.screener_sb_short)
      if self.is_visible(self.screener_sb_short) == True:
        open_tv_logger.warning('Failed to hide the Structure break screener indicator. The function will still continue on without exiting as this is not crucial.')
    
    # Change the candle type to a line
    candle_type = 'Line'
    if not self.change_candles_type(candle_type):
      open_tv_logger.warning(f'Failed to change the candle type to {candle_type}. Application will still continue on without exiting as this is not crucial.')

    #give it some time to rest
    sleep(2) 

    return True

  def re_setup(self):
    '''This resets the setup of TradingView so that the entries can get posted and `self.alerts.post_entries` can run smoothly'''
    # change to the screener layout (if we are on any other layout)
    if not self.change_layout(LAYOUT_NAME):
      self.change_layout(LAYOUT_NAME) # try once more
      if self.current_layout() != LAYOUT_NAME:
        open_tv_logger.error(f'Cannot change the layout to {LAYOUT_NAME}. Exiting function')
        return False
      
    # save the layout if it's the screener layout
    if not self.save_layout():
      if not self.save_layout(): # try once more
        open_tv_logger.warning(f'Cannot save the current layout {LAYOUT_NAME}. Exiting function')
        return False
    
    # verify that all required indicators are present on the chart
    screener_ob_check = self.get_indicator(self.screener_ob_short)
    screener_nw_check = self.get_indicator(self.screener_nw_short)
    screener_sb_check = self.get_indicator(self.screener_sb_short)
    drawer_check = self.get_indicator(self.drawer_shorttitle)

    if screener_ob_check is None: # try once more to find the Order Block screener
      screener_ob_check = self.get_indicator(self.screener_ob_short)

    if screener_nw_check is None: # try once more to find the Nadaraya Watson screener
      screener_nw_check = self.get_indicator(self.screener_nw_short)

    if screener_sb_check is None: # try once more to find the Structure break screener
      screener_sb_check = self.get_indicator(self.screener_sb_short)

    if drawer_check is None: # try once more to find the trade drawer
      drawer_check = self.get_indicator(self.drawer_shorttitle)

    if (screener_ob_check is None or screener_nw_check is None or 
        screener_sb_check is None or drawer_check is None):
      open_tv_logger.error(f'One or more indicators not found. Exiting function. Order Block: {screener_ob_check}, Nadaraya Watson: {screener_nw_check}, Structure break: {screener_sb_check}, Trade Drawer: {drawer_check}')
      return False

    # make the Trade Drawer indicator visible
    if not self.indicator_visibility(True, self.drawer_shorttitle):
      self.indicator_visibility(True, self.drawer_shorttitle)
      if self.is_visible(self.drawer_shorttitle) == False:
        open_tv_logger.warning('Failed to make the Trade Drawer indicator visible. The function will still continue on without exiting as this is not crucial.')
        
		# Change the candle type to a line
    candle_type = 'Line'
    if not self.change_candles_type(candle_type):
      open_tv_logger.warning(f'Failed to change the candle type to {candle_type}. Application will still continue on without exiting as this is not crucial.')
    
    #give it some time to rest
    sleep(2) 

    return True

  def set_bulk_alerts(self):
    '''
    This goes over every sublist in `symbol_sublists`. Each sublist has symbols. It opens a chart with the symbol as `symbol_sublist[0]`. 
    Then, it fills up the settings of all 3 screeners with symbols. Then alerts get set for all 3 screeners.
    Note: Sometimes, when alerts are made, the alerts are duplicated. 2 alerts are made on the same chart with the same symbols. I don't know why. It has been decided that this won't be fixed because it is unnecessary.
    '''
    symbol_sublists = symbol_sublist_gen()
    for symbol_sublist in symbol_sublists: # this will go through each set of the symbols in a category (this is a generator)
      try:
        chart_symbol = symbol_sublist[0] # the chart's symbol is the first symbol in the set
        if not self.open_chart.change_symbol(chart_symbol): # change chart's symbol
          open_tv_logger.error(f'Failed to change the chart\'s symbol to {chart_symbol}. Going to try with the next set of symbols for this category (if there are sets left)')
          continue
        
        # Configure all 3 screeners with the symbols
        if not self.change_settings(symbol_sublist): # input the symbols in all screeners' inputs
          open_tv_logger.error('Failed to change screeners\'s symbol settings. Going to try with the next set of symbols for this category (if there are sets left)')
          continue
        
        sleep(3) # wait for the screener indicators to fully load (we are avoiding to wait for the indicators to load as it will take too long)
        
        # Set alerts for all 3 screeners
        if not self.set_alerts(symbol_sublist): # set alerts for all 3 screeners
          open_tv_logger.error('Failed to set alerts for all screeners. Going to try with the next set of symbols for this category (if there are sets left)')
          continue
          
        sleep(5) # wait for 5 secs instead of waiting for the alerts to show up (it might be unnecessary)
      except Exception as e:
        open_tv_logger.exception(f'An error happened in set_bulk_alerts. Will continue with the next alerts. Error: {e}')
        continue 
        
  def change_layout(self, layout_name):
    '''This changes the layout of the chart to `layout_name` if we are a different one. If we are on the same layout, it does nothing.'''
    try:
      # switch the layout if we are on some other layout. if we are on the screener layout, we don't need to do anything
      curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
      if curr_layout.find_element(By.CSS_SELECTOR, '.text-yyMUOAN9').text == layout_name:
        return True

      # click on the dropdown arrow
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/div/button'))).click()
      
      # choose the screener layout
      layouts = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/a')))

      for layout in layouts:
        if layout.find_element(By.CSS_SELECTOR, '.layoutTitle-yyMUOAN9').text == layout_name:
          layout.click()
          return True
    except Exception as e:
      open_tv_logger.exception(f'An error happened when changing the layout. Error: ')
      return False
    
  def current_layout(self):
    '''This returns the current layout of the chart.'''
    try:
      curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
      return curr_layout.find_element(By.CSS_SELECTOR, '.text-yyMUOAN9').text
    except Exception as e:
      open_tv_logger.exception(f'An error happened when getting the current layout. Error: ')
      return ''

  def save_layout(self):
    '''This saves the current layout of the chart by clicking on the current layout.'''
    try:
      # check if the layout has been saved. If it hasn't, save it.
      curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
      if 'hidden'not in curr_layout.find_element(By.CSS_SELECTOR, '.saveString-XVd1Kfjg').get_attribute('class'):
        curr_layout.click()
        open_tv_logger.exception(f'Saved the current layout!')

      return True
    
    except Exception as e:
      open_tv_logger.exception(f'An error happened when saving the layout. Error: ')
      return False

  def change_settings(self, symbols_list, screener_shorttitle=None):
    '''This changes the settings of a screener. It fills in the symbols and clicks on Submit.
    
    Args:
        symbols_list: List of symbols to input into the screener
        screener_shorttitle: The short title of the screener to configure. If None, uses all 3 screeners.
    '''
    try:
      # Determine which screeners to configure
      screeners_to_configure = []
      if screener_shorttitle:
        # Configure specific screener - get fresh indicator reference
        if screener_shorttitle == self.screener_ob_short:
          indicator = self._safe_indicator_access(self.screener_ob_short)
          screeners_to_configure = [(self.screener_ob_short, indicator)]
        elif screener_shorttitle == self.screener_nw_short:
          indicator = self._safe_indicator_access(self.screener_nw_short)
          screeners_to_configure = [(self.screener_nw_short, indicator)]
        elif screener_shorttitle == self.screener_sb_short:
          indicator = self._safe_indicator_access(self.screener_sb_short)
          screeners_to_configure = [(self.screener_sb_short, indicator)]
        else:
          open_tv_logger.error(f'Unknown screener shorttitle: {screener_shorttitle}')
          return False
      else:
        # Configure all 3 screeners - get fresh indicator references
        screeners_to_configure = [
          (self.screener_ob_short, self._safe_indicator_access(self.screener_ob_short)),
          (self.screener_nw_short, self._safe_indicator_access(self.screener_nw_short)),
          (self.screener_sb_short, self._safe_indicator_access(self.screener_sb_short))
        ]
      
      # Configure each screener
      all_success = True
      for shorttitle, screener in screeners_to_configure:
        if not screener:
          open_tv_logger.error(f'Could not find screener indicator: {shorttitle}. Skipping.')
          all_success = False
          continue
        
        try:
          # Open its settings
          screener.click()
          WebDriverWait(screener, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-name="legend-settings-action"]'))).click()
          settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
          symbol_inputs = settings.find_elements(By.CSS_SELECTOR, '.inlineRow-tBgV1m0B div[data-name="edit-button"]') # symbol inputs

          # change the symbol inputs based on the total number of symbols
          for i, to_be_symbol in enumerate(symbols_list):
            symbol_inputs[i].click()
            search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input')
            search_input.send_keys(to_be_symbol)
            search_input.send_keys(Keys.ENTER)

          # Handle the 3 timeframe inputs
          open_tv_logger.info(f'Setting timeframe inputs for screener {shorttitle}')
          timeframe_inputs = settings.find_elements(By.CSS_SELECTOR, 'div[class="cell-tBgV1m0B"] div[class="inner-tBgV1m0B"] span')
          
          # Get the first 3 timeframe elements
          if len(timeframe_inputs) >= 3:
            # Import timeframe constants here to avoid circular import
            from main import SCREENER_TIMEFRAME_1, SCREENER_TIMEFRAME_2, SCREENER_TIMEFRAME_3, TIMEFRAME_ID_MAP
            timeframes = [SCREENER_TIMEFRAME_1, SCREENER_TIMEFRAME_2, SCREENER_TIMEFRAME_3]
            
            for idx, (tf_input, timeframe) in enumerate(zip(timeframe_inputs[:3], timeframes)):
              try:
                # Click on the timeframe input to open dropdown
                tf_input.click()
                sleep(0.5)  # Small delay to ensure dropdown opens
                
                # Find the popup menu container in the root driver
                popup_menu = WebDriverWait(self.driver, 5).until(
                  EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="popup-menu-container"]'))
                )
                
                # Get the corresponding ID for this timeframe
                if timeframe in TIMEFRAME_ID_MAP:
                  timeframe_id = TIMEFRAME_ID_MAP[timeframe]
                  
                  # Find and click the option with the matching ID
                  option = popup_menu.find_element(By.ID, timeframe_id)
                  
                  # Scroll the option into view if needed
                  self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
                  sleep(0.2)
                  
                  option.click()
                  open_tv_logger.info(f'Set timeframe {idx + 1} to: {timeframe}')
                  sleep(0.5)  # Small delay before next timeframe
                else:
                  open_tv_logger.error(f'Timeframe "{timeframe}" not found in TIMEFRAME_ID_MAP')
                  
              except Exception as e:
                open_tv_logger.error(f'Error setting timeframe {idx + 1}: {e}')
          else:
            open_tv_logger.warning(f'Found only {len(timeframe_inputs)} timeframe inputs, expected at least 3')

          # click on submit
          self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
          open_tv_logger.info(f'Successfully changed the inputs of screener {shorttitle}: {symbols_list}')
          sleep(2)  # Give time for settings to apply before moving to next screener
        except Exception as e:
          open_tv_logger.exception(f'Error occurred when filling in the inputs of screener {shorttitle}. Error:')
          all_success = False
          
      return all_success
    except Exception as e:
      open_tv_logger.exception('Error occurred when configuring screeners. Error:')
      return False

  def open_alerts_sidebar(self):
    '''opens the alerts sidebar if it is closed. If it is already open, it does nothing'''
    try:
      alert_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="right-toolbar"] button[aria-label="Alerts"]')))
      if alert_button.get_attribute('aria-pressed') == 'false':
        alert_button.click()
        open_tv_logger.info('Successfully opened the alerts sidebar!')
        return True
      else: # if the alerts sidebar is already open
        open_tv_logger.info('The alerts sidebar is already open!')
        return True
    except Exception as e:
      open_tv_logger.exception(f'An error happened when opening the alerts sidebar. Error: ')
      return False

  def change_candles_type(self, candle_type: str):
    """
    Changes the candle type to `candle_type` if it isn't already so. 
      
    Args:
    candle_type (str): Can be either "Line" or "Candle".

    Returns:
    bool: True if the candle type was changed successfully, False otherwise.
    """
    try:
        # Find the candle button
        candle_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id="header-toolbar-chart-styles"] button'))
        )
        
        # If the style of the candle is not candle_type
        if candle_type not in candle_button.get_attribute('aria-label'):
            open_tv_logger.info(f'Changing the style of candles to {candle_type}')
            candle_button.click()
            
            # Wait for the dropdown menu to appear
            menu = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]'))
            )
            
            # Find the Line type and click on it
            candle_types = WebDriverWait(menu, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-role="menuitem"]'))
            )
            for c in candle_types:
                if c.get_attribute('data-value') == candle_type.lower():
                    c.click()
                    open_tv_logger.info('Found Line candle type!')
                    return True
        else:
            open_tv_logger.info(f'The candle type is already {candle_type}.')
            return True
    except Exception as e:
        open_tv_logger.error(f"Error in changing candle type: {e}")
        return False
		
  def _reinitialize_screener_indicator(self, shorttitle):
    '''Re-initializes a screener indicator after it has been re-uploaded to avoid stale element errors.
    
    Args:
        shorttitle: The short title of the screener to re-initialize
        
    Returns:
        The re-initialized indicator element, or None if not found
    '''
    if shorttitle == self.screener_ob_short:
      self.screener_ob_indicator = self.get_indicator(self.screener_ob_short)
      return self.screener_ob_indicator
    elif shorttitle == self.screener_nw_short:
      self.screener_nw_indicator = self.get_indicator(self.screener_nw_short)
      return self.screener_nw_indicator
    elif shorttitle == self.screener_sb_short:
      self.screener_sb_indicator = self.get_indicator(self.screener_sb_short)
      return self.screener_sb_indicator
    return None

  def set_alerts(self, symbols, screener_shorttitle=None):
    '''This first checks if the screener(s) have an error. If they do, it re-uploads them and fills in the symbols again. 
    If an error is still there, `False` is returned. If there was no error in the first place, alerts get created.
    
    Args:
        symbols: List of symbols to set alerts for
        screener_shorttitle: The short title of a specific screener to set alerts for. If None, sets alerts for all 3 screeners.
    '''
    # Determine which screeners to set alerts for - get fresh references
    screeners_to_alert = []
    if screener_shorttitle:
      # Set alert for specific screener
      if screener_shorttitle == self.screener_ob_short:
        indicator = self._safe_indicator_access(self.screener_ob_short)
        screeners_to_alert = [(self.screener_ob_short, indicator, self.screener_ob_name)]
      elif screener_shorttitle == self.screener_nw_short:
        indicator = self._safe_indicator_access(self.screener_nw_short)
        screeners_to_alert = [(self.screener_nw_short, indicator, self.screener_nw_name)]
      elif screener_shorttitle == self.screener_sb_short:
        indicator = self._safe_indicator_access(self.screener_sb_short)
        screeners_to_alert = [(self.screener_sb_short, indicator, self.screener_sb_name)]
      else:
        open_tv_logger.error(f'Unknown screener shorttitle: {screener_shorttitle}')
        return False
    else:
      # Set alerts for all 3 screeners - get fresh references
      screeners_to_alert = [
        (self.screener_ob_short, self._safe_indicator_access(self.screener_ob_short), self.screener_ob_name),
        (self.screener_nw_short, self._safe_indicator_access(self.screener_nw_short), self.screener_nw_name),
        (self.screener_sb_short, self._safe_indicator_access(self.screener_sb_short), self.screener_sb_name)
      ]
    
    all_success = True
    for shorttitle, indicator, name in screeners_to_alert:
      try:
        # check if the screener indicator has an error
        if not self.is_no_error(shorttitle):
          open_tv_logger.error(f'Screener {shorttitle} had an error. Could not set an alert for this tab. Trying to reupload indicator')
          if not self.reupload_indicator(indicator, name, shorttitle):
            open_tv_logger.error(f'Could not re-upload screener {shorttitle}. Cannot set an alert for the screener.')
            all_success = False
            continue
          
          # Re-initialize the screener indicator after re-uploading (to prevent StaleElementReferenceException)
          indicator = self._reinitialize_screener_indicator(shorttitle)
          if not self.change_settings(symbols, shorttitle):
            open_tv_logger.error(f'Could not input the symbols into screener {shorttitle}. Cannot set an alert for the screener.')
            all_success = False
            continue
          sleep(5) # wait for the screener indicator to fully load
          if not self.is_no_error(shorttitle): # if an error is still there
            open_tv_logger.error(f'Error is still there in screener {shorttitle}. Cannot set an alert for the screener.')
            all_success = False
            continue
       
        # set the alert for the screener
        if not self.click_create_alert(shorttitle, name):
          if self.reupload_indicator(indicator, name, shorttitle): # Reuploading the screener
            # Re-initialize the screener indicator after re-uploading (to prevent StaleElementReferenceException)
            indicator = self._reinitialize_screener_indicator(shorttitle)
            if self.change_settings(symbols, shorttitle):
              if not self.click_create_alert(shorttitle, name):
                all_success = False
            else:
              all_success = False
          else:
            all_success = False
            
      except Exception as e:
        open_tv_logger.exception(f'Error occurred when setting up alert for screener {shorttitle}. Error:')
        all_success = False
        
    return all_success

  def click_create_alert(self, shorttitle, alert_name=''):
    '''This clicks the + button to create an alert for the indicator with the shorttitle of `shorttitle`, names the alert to `alert_name` if it's not an empty string otherwise no name will be given and the default alert name will be used. Then, "Create" gets clicked. This returns `True` if the alert was created otherwise `False`. If something goes wrong, the "Create Alert" popup will be closed (if it was open) and `False` will be returned.'''
    try:
      self.utils.open_alert_tab(self.driver) # Make sure that the Alerts tab is open

      # click on the + button
      plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
      plus_button.click()
        
      # wait for the create alert popup to show and click the dropdown 
      popup = None
      try:
        popup = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
      except TimeoutException:
        self.driver.get(self.driver.current_url) # If the popup doesn't show up within 5 seconds, refresh the page and try again. I can't use self.driver.refresh() because that might trigger a Google popup asking you if you want to refresh the page. I don't think PYthon can control Google popups
        sleep(3) # wait for the page to load after refreshing
        open_tv_logger.error('Popup did not show up within 5 seconds. Page refreshed. Trying to create alert again.')
        plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
        plus_button.click()
      
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-qa-id="ui-kit-disclosure-control main-series-select"]'))).click()
    
      # choose the indicator
      indicator_found = False
      for el in self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'):
        if shorttitle in el.text:
          indicator_found = True
          el.click()
          break    

      if not indicator_found: # if the indicator is not found, close the "Create Alert" popup and exit
        open_tv_logger.error(f'Failed to create alert. {shorttitle} is unavailable in the dropdown. Closing popup and exiting.')
        popup.find_element(By.CSS_SELECTOR, 'button[data-name="close"]').click()
        return False
   
      # click on submit if the indicator was available in the dropdown and was selected
      if indicator_found:
        self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]').click()
        open_tv_logger.info('Clicked on "Create"!')

        # wait for the alert to be created
        try:
          WebDriverWait(self.driver, 2.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"] div[data-name="error-hint"]')))
        except:
          open_tv_logger.info('No error occured while saving alert!')
          return True
        else:
          open_tv_logger.error('Alert failed to get saved. Clicking on "Cancel".')
          self.driver.find_element(By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"] button[data-name="cancel"]').click()
          return False
        
    except Exception as e:
      # close the "Create Alert" popup if an alert fails to get created
      popup = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
      if popup: 
        if popup.find_elements(By.CSS_SELECTOR, 'button[data-name="close"]'):
          popup.find_element(By.CSS_SELECTOR, 'button[data-name="close"]').click()
      open_tv_logger.exception('Error occurred when setting up alert. Exiting function. Error:')
      return False
    
    return False
  
  def indicator_visibility(self, make_visible: bool, shorttitle: str):
    '''Makes `shorttitle` indicator visible or hidden by clicking on the indicator's 👁️ button'''
    HIDDEN = 'Hidden'
    VISIBLE = 'Visible'

    # get the indicator - always get fresh reference
    indicator = self._safe_indicator_access(shorttitle)

    try:
      if indicator != None: # that means that we've found our indicator
        eye = indicator.find_element(By.CSS_SELECTOR, 'button[data-name="legend-show-hide-action"]')
        current_visibility = VISIBLE if 'Hide' in eye.get_attribute('aria-label') else HIDDEN
        
        if make_visible == True: # make the indicator visible
          if current_visibility == HIDDEN:
            indicator.click()
            eye.click()
            open_tv_logger.info(f'Successfully changed the visibility of {shorttitle} to make it visible!')
            return True
          if current_visibility == VISIBLE: 
            open_tv_logger.info(f'{shorttitle} indicator is already visible. No need to change its visibility!')
            return True

        if make_visible == False: # make the indicator hidden
          if current_visibility == VISIBLE:
            indicator.click()
            eye.click()
            open_tv_logger.info(f'Successfully changed the visibility of {shorttitle} to make it hidden!')
            return True
          if current_visibility == HIDDEN: 
            open_tv_logger.info(f'{shorttitle} indicator is already hidden. No need to change its visibility!')
            return True
    except Exception as e:
      open_tv_logger.exception(f'Error occurred when changing the visibility of {shorttitle} to make it {"visible" if make_visible else "hidden"}. Error: ')
      return False
    
    return False

  def is_visible(self, shorttitle: str):
    '''This returns `True` if the visibility of `shorttitle` indicator is shown. Otherwise, this returns `False` if its visibility is hidden.'''
    # get the indicator - always get fresh reference
    indicator = self._safe_indicator_access(shorttitle)
      
    # check its visibility
    try:
      if indicator != None: # that means that we've found our indicator
        status = 'Hidden' if 'disabled' in indicator.get_attribute('class') else 'Shown'
        open_tv_logger.info(f'{shorttitle} indicator is {status}.')
        return status == 'Shown'
    except Exception as e:
      open_tv_logger.exception(f'Error ocurred when checking the visibility of {shorttitle} indicator. Error:')
      return False
    
    return False

  def is_no_error(self, shorttitle:str):
    '''
    this checks if the indicator has successfully loaded without an error. Returns `True` if it has no error but `False` if there is an error.
    '''
    try:
      # find the indicator - always get fresh reference to avoid stale element
      indicator = self._safe_indicator_access(shorttitle)

      # if there is no error
      if indicator and indicator.find_elements(By.CSS_SELECTOR, '.statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS') == []:
        open_tv_logger.info(f'There is no error in {shorttitle}!')
        return True
      
      open_tv_logger.error(f'There is an error in {shorttitle}.')
      return False
    except StaleElementReferenceException:
      open_tv_logger.warning(f'Stale element when checking error for {shorttitle}, trying to get fresh reference')
      try:
        indicator = self._get_fresh_indicator(shorttitle)
        if indicator and indicator.find_elements(By.CSS_SELECTOR, '.statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS') == []:
          open_tv_logger.info(f'There is no error in {shorttitle}!')
          return True
        open_tv_logger.error(f'There is an error in {shorttitle}.')
        return False
      except Exception as e:
        open_tv_logger.exception(f'Error occurred even after retry for {shorttitle}. Error:')
        return False
    except Exception as e:
      open_tv_logger.exception(f'Error ocurred when checking if {shorttitle} had an error. Error:')
      return False
    
  def delete_all_alerts(self):
    '''Waits for the alert sidebar to show up and checks if there are any alerts. If there are, they are deleted by making all the alerts inactive and then deleting the inactive alerts. Then it waits a second.'''
    dropdown_option_selector = 'div.item-jFqVJoPk'

    def open_dropdown():
      '''If the drpodown isn't already open, clicks the 3 dots and returns the dropdown that opens '''
      # if the dropdown menu isn't already open
      if not self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="menu-inner"]'):
        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))).click()
      return WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]')))

    try:
      # Make sure that the Alerts tab is open
      self.utils.open_alert_tab(self.driver)

      # Check if there already are no alerts
      if self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5') == []:
        open_tv_logger.info('There are no alerts. No need to delete any alerts!')
        return True

      dropdown = open_dropdown()

      # Check if "Stop All" is disabled
      stop_all_button = WebDriverWait(dropdown, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, dropdown_option_selector)))[1]
      if 'isDisabled' in stop_all_button.get_attribute('class'):
        open_tv_logger.info('The "Stop All" option is disabled. No need to click it.')
      else:
        stop_all_button.click()
        self.utils.click_yes_in_confirm_popup(self.driver)
      
      dropdown = open_dropdown()

      # Check if "Delete All Inactive" is disabled
      delete_inactive_button = WebDriverWait(dropdown, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, dropdown_option_selector)))[2]
      if 'isDisabled' in delete_inactive_button.get_attribute('class'):
        open_tv_logger.info('The "Delete All Inactive" option is disabled. No need to click it.')
      else:
        delete_inactive_button.click()
        self.utils.click_yes_in_confirm_popup(self.driver)

      return True
    except Exception as e:
      open_tv_logger.exception(f'Error happened somewhere when deleting all alerts. Failed to delete all alerts. Error:')
      return False

  def reupload_indicator(self, indicator, indicator_name, indicator_shorttitle):
    '''removes indicator and reuploads it again to the chart by clicking on the screener in the Favorites dropdown. It then waits for the indicator to show up on the chart and returns `True` if it does otherwise `False`.

    Don't remove the print statements. It seems like the code will only run with the print statements.'''
    val = False

    try:
      # Get fresh indicator reference to avoid stale element
      fresh_indicator = self._safe_indicator_access(indicator_shorttitle)
      if not fresh_indicator:
        open_tv_logger.error(f'Could not get fresh reference to {indicator_shorttitle}')
        return False
        
      # click on the indicator
      fresh_indicator.click()

      # click on data-name="legend-delete-action" (a sub element under the indicator)
      delete_action = WebDriverWait(fresh_indicator, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-name="legend-delete-action"]')))
      print('Found remove button: ', delete_action)
      delete_action.click()

      # click on "Favorites" dropdowm
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[id="header-toolbar-indicators"] button[data-name="show-favorite-indicators"]'))).click()
      print('favorites dropdown was clicked')

      # Wait for the dropdown menu to appear
      menu = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]')))
      print('dropdown menu appeared')

      # find the indicator in the dropdown menu and click on it
      dropdown_indicators = WebDriverWait(menu, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-role="menuitem"]')))
      for el in dropdown_indicators:
        print('current indicator: ',el)
        text = el.find_element(By.CSS_SELECTOR, 'span[class="label-l0nf43ai apply-overflow-tooltip"]').text
        if indicator_name == text:
          print(f'Found {indicator_name}')
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
          if ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text == indicator_shorttitle:
            val = True
            break
        if val: # if the indicator is found on the chart, break the while loop
          open_tv_logger.info(f'{indicator_shorttitle} is on the chart after re-uploading it!')
          break
    except Exception as e:
      open_tv_logger.exception(f'An error occurred when re-uploading {indicator_shorttitle}. Could not reupload {indicator_shorttitle}. Error: {e}')
      return False

    return val

  def get_indicator(self, ind_shorttitle: str):
    '''Returns the indicator which has the same shorttitle as `ind_shorttitle`. If an indicator with the same shorttitle can't be found or an error occurs, `None` will be returned'''
    try:
      indicator = None
      sleep(3) # wait for the chart to load
      wait = WebDriverWait(self.driver, 15)
      indicators = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')))
      
      for ind in indicators: 
        indicator_name = ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text
        if indicator_name == ind_shorttitle: # finding the indicator
          open_tv_logger.info(f'Found indicator {ind_shorttitle}!')
          indicator = ind
          break
    except Exception as e:
      open_tv_logger.exception(f'Failed to find indicator {ind_shorttitle}. Error:')
      return None

    return indicator
    
  def _get_fresh_indicator(self, ind_shorttitle: str):
    '''Always gets a fresh reference to the indicator to avoid stale element errors'''
    return self.get_indicator(ind_shorttitle)
    
  def _safe_indicator_access(self, shorttitle: str, max_retries: int = 2):
    '''Safely access an indicator with retry logic for stale element exceptions'''
    for attempt in range(max_retries):
      try:
        indicator = self._get_fresh_indicator(shorttitle)
        if indicator:
          # Test if the element is still valid by accessing a property
          _ = indicator.get_attribute('class')
          return indicator
      except StaleElementReferenceException:
        if attempt < max_retries - 1:
          open_tv_logger.warning(f'Stale element for {shorttitle}, retrying... (attempt {attempt + 1})')
          sleep(1)
        else:
          open_tv_logger.error(f'Failed to get fresh indicator {shorttitle} after {max_retries} attempts')
    return None
    
  def current_chart_tframe(self):
    '''Returns the current chart's timeframe'''
    try:
      tf_button = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))
      return tf_button.get_attribute('aria-label')
    except Exception as e:
      open_tv_logger.exception(f'Failed to get the current chart timeframe. Error:')
      return ''
    
  def is_alerts_sidebar_open(self):
    '''This checks if the Alerts sidebar is open. Returns `True` if it is and returns `False` if it is not.'''
    try:
      alert_button = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="right-toolbar"] button[aria-label="Alerts"]')))
      if alert_button.get_attribute('aria-pressed') == 'true': # if the alerts sidebar is open
        open_tv_logger.info('The Alerts sidebar is open!')
        return True
      else:
        open_tv_logger.info('The Alerts sidebar is closed.')
        return False
    except Exception as e:
      open_tv_logger.exception(f'Failed to check if the Alerts sidebar is open. Error: ')
      return False    
  
  def no_alerts(self):
    '''This checks if there no alerts. If there are no alerts, returns `True` and returns `False` if there are alerts'''
    try:
      self.utils.open_alert_tab(self.driver) # Make sure that the Alerts tab is open
      alerts = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="widget-X9EuSe_t widgetbar-widget widgetbar-widget-alerts"] div[class="itemBody-ucBqatk5 active-Bj96_lIl"]')))
      if not alerts: # if there are no alerts
        open_tv_logger.info('There are no alerts!')
        return True
      else:
        open_tv_logger.info('There are alerts!')
        return False
    except Exception as e:
      open_tv_logger.exception(f'Failed to check if there are no alerts. Error: ')
      return False
