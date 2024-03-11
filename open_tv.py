'''
the main things that this does is:
opens Tradingview, sets it up, sets alerts for all the symbols, changes the layout, changes the screener's settings, creates an alert for the screener, changes the visibility of the indicators, deletes all the alerts and re-uploads the screener on the chart.

There are a few other things this does that are related to all the things mentioned above.
'''

# import modules
import get_alert_data
import logger_setup
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
from selenium.common.exceptions import WebDriverException, TimeoutException

# Set up logger for this file
open_tv_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

# some constants
SYMBOL_INPUTS = 5 #number of symbol inputs in the screener
CHART_TIMEFRAME = '1 hour' # the timeframe that the entries are from
USED_SYMBOLS_INPUT = "Used Symbols" # Name of the Used Symbols input in the Screener
LAYOUT_NAME = 'Screener' # Name of the layout for the screener
SCREENER_REUPLOAD_TIMEOUT = 15 # seconds to wait for the screener to show up on the chart after re-uploading it

CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
# CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'

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

  def __init__(self, keep_open: bool, screener_shorttitle: str, screener_name: str, drawer_shorttitle: str, drawer_name: str, interval_minutes: int, start_fresh: bool) -> None:
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
    self.interval_seconds = interval_minutes * 60 # Convert the interval to seconds
    self.start_fresh = start_fresh
    self.init_succeeded = True
    if start_fresh: 
      if not fill_symbol_set(SYMBOL_INPUTS): # Call the function to fill up symbol_set in symbol_settings.py
        open_tv_logger.error(f'Cannot fill up the symbol set. Exiting function')
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

  def setup_tv(self, trim_file, log_file, LINES_TO_KEEP):
    '''This opens tradigview, changes the layout of the chart, saves the layout if `LAYOUT_NAME` == 'Screener', opens the alert sidebar, deletes all alerts, gets access to the screener & trade drawer indicators, makes them both visible and changes the timeframe of the screener'''
    # open tradingview
    if not self.open_page('https://www.tradingview.com/chart'):
      if not self.open_page('https://www.tradingview.com/chart'): # try once more
        open_tv_logger.error(f'Failed to open tradingview. Exiting function')
        return False

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

    # set the timeframe to 1H 
    if not self.open_chart.change_tframe(CHART_TIMEFRAME):
      self.open_chart.change_tframe(CHART_TIMEFRAME) # try once more
      if not self.current_chart_tframe() == CHART_TIMEFRAME:
        open_tv_logger.error(f'Cannot change the chart timeframe to {CHART_TIMEFRAME}. Exiting function')
        return False

    # open the alerts sidebar
    if not self.open_alerts_sidebar():
      self.open_alerts_sidebar() # try once more
      if not self.alerts_sidebar_open():
        open_tv_logger.error(f'Cannot open the alerts sidebar. Exiting function')
        return False

    # delete all alerts
    if self.start_fresh:
      if not self.delete_all_alerts():
        self.delete_all_alerts() # try once more
        if not self.no_alerts():
          open_tv_logger.error(f'Cannot delete all alerts. Exiting function')
          return False

    # make the screener and the trade drawer indicator into attributes of this object
    self.screener_indicator = self.get_indicator(self.screener_shorttitle)
    self.drawer_indicator = self.get_indicator(self.drawer_shorttitle)

    if self.screener_indicator is None: # try once more to find the screener
      self.screener_indicator = self.get_indicator(self.screener_shorttitle)

    if self.drawer_indicator is None: # try once more to find the trade drawer
      self.drawer_indicator = self.get_indicator(self.drawer_shorttitle)

    if self.screener_indicator is None or self.drawer_indicator is None:
      open_tv_logger.error(f'One of the indicators is not found. Exiting function. Screener: {self.screener_indicator}, Trade Drawer: {self.drawer_indicator}')
      return False

    self.alerts = get_alert_data.Alerts(self.drawer_shorttitle, self.screener_shorttitle, self.driver, CHART_TIMEFRAME, self.interval_seconds, trim_file, log_file, LINES_TO_KEEP)

    # make the screener visible and Trade Drawer indicator visible
    if not self.indicator_visibility(True, self.screener_shorttitle):
      self.indicator_visibility(True, self.screener_shorttitle)
      if self.is_visible(self.screener_shorttitle) == False:
        open_tv_logger.warning('Failed to make the screener indicator visible. The function will still continue on without exiting as this is not crucial.')

    if not self.indicator_visibility(True, self.drawer_shorttitle):
      self.indicator_visibility(True, self.drawer_shorttitle)
      if self.is_visible(self.drawer_shorttitle) == False:
        open_tv_logger.warning('Failed to make the Trade Drawer indicator visible. The function will still continue on without exiting as this is not crucial.')
    
    #give it some time to rest
    sleep(2) 

    return True

  def set_bulk_alerts(self):
    '''
    This goes over every sublist in `symbol_sublists`. Each sublist has symbols. It opens a chart with the symbol as `symbol_sublist[0]`. Then, it fills up the settings of the screener with symbols. Then an alert gets set for the screener.
    Note: Sometimes, when alerts are made, the alerts are duplicated. 2 alerts are made on the same chart with the same symbols. I don't know why. It has been decided that this won't be fixed because it is unnecessary.
    '''
    symbol_sublists = symbol_sublist_gen()
    for symbol_sublist in symbol_sublists: # this will go through each set of the symbols in a category (this is a generator)
      try:
        chart_symbol = symbol_sublist[0] # the chart's symbol is the first symbol in the set
        if not self.open_chart.change_symbol(chart_symbol): # change chart's symbol
          open_tv_logger.error(f'Failed to change the chart\'s symbol to {chart_symbol}. Going to try with the next set of symbols for this category (if there are sets left)')
          continue
        if not self.change_settings(symbol_sublist): # input the symbols in the screener's inputs
          open_tv_logger.error('Failed to change screener\'s symbol settings. Going to try with the next set of symbols for this category (if there are sets left)')
          continue
        sleep(3) # wait for the screener indicator to fully load (we are avoiding to wait for the indicator to load as it will take too long)
        if not self.set_alerts(symbol_sublist): # wait for the screener to load and set an alert for it
          open_tv_logger.error('Failed to set alert for screener. Going to try with the next set of symbols for this category (if there are sets left)')
          continue
        sleep(5) # wait for 5 secs instead of waiting for the alert to show up (it might be unnecessary)
      except Exception as e:
        open_tv_logger.exception(f'An error happened in set_bulk_alerts. Will continue with the next alerts. Error: ')
        continue 
        
  def change_layout(self, layout_name):
    '''This changes the layout of the chart to `layout_name` if we are a different one. If we are on the same layout, it does nothing.'''
    try:
      # switch the layout if we are on some other layout. if we are on the screener layout, we don't need to do anything
      curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
      if curr_layout.find_element(By.CSS_SELECTOR, '.text-yyMUOAN9').text == layout_name:
        return True

      # click on the dropdown arrow
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/button[2]'))).click()
      
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
    '''This saves the current layout of the chart.'''
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

  def change_settings(self, symbols_list):
    '''This changes the settings of the screener. It first fills in the "Used Symbols" input to tell the indicator how many symbols we're going to use. Then it fills in the symbols and clicks on Submit.'''
    try:
      # find the settings popup
      settings = None
      screener = self.get_indicator(self.screener_shorttitle)  # get the screener
      if not screener:
        open_tv_logger.error(f'Could not find screener indicator: {screener}. Exiting function.')
        return False
      
      # Open its settings
      self.screener_indicator = screener
      self.screener_indicator.click()
      WebDriverWait(self.screener_indicator, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-settings-action"]'))).click()
      settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
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
      open_tv_logger.info(f'Successfully changed the inputs of the screener: {symbols_list}')
      return True
    except Exception as e:
      open_tv_logger.exception('Error ocurred when filling in the inputs of the screener. Error:')
      return False

  def change_get_exit_settings(self, entry_time, entry_price, entry_type, sl_price, tp1_price, tp2_price, tp3_price):
    try:
      # double click on the indicator so that the settings can open 
      i = 1
      while i <= 3:
        try:
          self.get_exits_indicator = self.get_indicator(self.get_exits_shorttitle)
          ActionChains(self.driver).move_to_element(self.get_exits_indicator).perform()
          ActionChains(self.driver).double_click(self.get_exits_indicator).perform()
          settings = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="indicator-properties-dialog"]')))
          break
        except Exception as e:
          open_tv_logger.exception('Failed to open Get Exit\'s settings. Error:')
          i += 1
          if i == 4:
            open_tv_logger.error('Get Exit indicator\'s settings failed to open. Could not change the settings. Exiting function.')
            return False
        
      # when the settings come up, click on the Inputs tab (just in case we’re on some other tab)
      settings.find_element(By.CSS_SELECTOR, 'div[class="tabs-vwgPOHG8"] button[id="inputs"]').click()

      # fill up the settings
      inputs = settings.find_elements(By.CSS_SELECTOR, '.cell-tBgV1m0B input')
      for i in range(len(inputs)):
        val = 0
        if i == 0:
          val = entry_time
        elif i == 1:
          val = entry_price
        elif i == 2:
          val = entry_type
        elif i == 3:
          val = sl_price
        elif i == 4:
          val = tp1_price
        elif i == 5:
          val = tp2_price
        elif i == 6:
          val = tp3_price

        ActionChains(self.driver).key_down(Keys.CONTROL, inputs[i]).send_keys('a').perform()
        inputs[i].send_keys(Keys.DELETE)
        inputs[i].send_keys(val)

      open_tv_logger.info(f'Get Exits\'s settings changed. Inputs: entry_time - {entry_time}, entry_price - {entry_price}, entry_type - {entry_type}, sl_price - {sl_price}, tp1_price - {tp1_price}, tp2_price - {tp2_price}, tp3_price - {tp3_price}')

      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
      return True
    except Exception as e:
      open_tv_logger.exception('Failed to change the Get Exits\'s settings. Error:')
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

  def set_alerts(self, symbols):
    '''This first checks if the screener has an error. If it does, it re-uploads it and fills in the symbols again. If an error is still there, `False` is returned. If there was no error in the first place, an alert gets created. If there was an error in creating the alert, it tries again.'''

    # check if the screener indicator has an error
    if not self.is_no_error(self.screener_shorttitle):
      open_tv_logger.error('Screener indicator had an error. Could not set an alert for this tab. Trying to reupload indicator')
      if not self.reupload_indicator(self.screener_indicator, self.screener_name, self.screener_shorttitle):
        open_tv_logger.error('Could not re-upload screener. Cannot set an alert for the screener. Exiting function.')
        return False
      if not self.change_settings(symbols):
        open_tv_logger.error('Could not input the symbols into the screener. Cannot set an alert for the screener. Exiting function.')
        return False
      sleep(5) # wait for the screener indicator to fully load (we are avoiding to wait for the indicator to load because it will take too long)
      if not self.is_no_error(self.screener_shorttitle): # if an error is still there
        open_tv_logger.error('Error is still there in the screener. Cannot set an alert for the screener. Exiting function.')
        return False
   
    # set the alert for the screener
    try:
      if not self.click_create_alert(self.screener_shorttitle):
        if self.reupload_indicator(self.screener_indicator, self.screener_name, self.screener_shorttitle): # Reuploading the screener
          if self.change_settings(symbols):
            return self.click_create_alert(self.screener_shorttitle)
      else:
        return True
    except Exception as e:
      open_tv_logger.exception('Error occurred when setting up alert. Exiting function. Error:')
      return False
    
    return False
  
  def set_get_exit_alert(self, alert_name, entry_time, entry_price, entry_type, sl_price, tp1_price, tp2_price, tp3_price):
    '''This first checks if the Get Exit indicator has an error. If it does, it re-uploads it and fills in the inputs again. If an error is still there, `False` is returned. If there was no error in the first place, an alert gets created. If there was an error in creating the alert, it tries again.'''

    # check if the indicator indicator has an error
    if not self.is_no_error(self.get_exits_shorttitle):
      open_tv_logger.error('indicator had an error. Could not set an alert for this tab. Trying to reupload indicator')
      if not self.reupload_indicator(self.get_exits_indicator, self.get_exits_name, self.get_exits_shorttitle):
        open_tv_logger.error('Could not re-upload indicator. Cannot set an alert for the indicator. Exiting function.')
        return False
      if not self.change_get_exit_settings(entry_time, entry_price, entry_type, sl_price, tp1_price, tp2_price, tp3_price):
        open_tv_logger.error('Could not input the settings. Cannot set an alert for the indicator. Exiting function.')
        return False
      sleep(5) # wait for the indicator to fully load (we are avoiding to wait for the indicator to load because it will take too long)
      if not self.is_no_error(self.get_exits_shorttitle): # if an error is still there
        open_tv_logger.error('Error is still there in the indicator. Cannot set an alert for the indicator. Exiting function.')
        return False
   
    # set the alert for the indicator
    try:
      if not self.click_create_alert(self.get_exits_shorttitle, alert_name):
        if self.reupload_indicator(self.get_exits_indicator, self.get_exits_name, self.get_exits_shorttitle): # Reuploading the indicator
          if self.change_get_exit_settings(entry_time, entry_price, entry_type, sl_price, tp1_price, tp2_price, tp3_price):
            return self.click_create_alert(self.get_exits_shorttitle, alert_name)
      else:
        return True
    except Exception as e:
      open_tv_logger.exception('Error occurred when setting up alert. Exiting function. Error:')
      return False
    
    return False

  def click_create_alert(self, shorttitle, alert_name=''):
    '''This clicks the + button to create an alert for the indicator with the shorttitle of `shorttitle`, names the alert to `alert_name` if it's not an empty string otherwise no name will be given and the default alert name will be used. Then, "Create" gets clicked. This returns `True` if the alert was created otherwise `False`. If something goes wrong, the "Create Alert" popup will be closed (if it was open) and `False` will be returned.'''
    try:
      # click on the + button
      plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
      plus_button.click()
        
      # wait for the create alert popup to show and click the dropdown 
      popup = None
      try:
        popup = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
      except TimeoutException:
        self.driver.get(self.driver.current_url) # If the popup doesn't show up within 5 seconds, refresh the page and try again. I can't use self.driver.refresh() because that might trigger a Google popup asking you if you want to refresh the page. I don't think PYthon can click control Google popups
        sleep(3) # wait for the page to load after refreshing
        open_tv_logger.error('Popup did not show up within 5 seconds. Page refreshed. Trying to create alert again.')
        plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
        plus_button.click()
      
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-name="main-series-select"]'))).click()
    
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
      
      if alert_name != '': # if an alert name is given, set it
        alert_name_input = popup.find_element(By.CSS_SELECTOR, 'input[id="alert-name"]')
        alert_name_input.send_keys(Keys.CONTROL + "a") # Clear the field by sending Ctrl+A and then Backspace
        alert_name_input.send_keys(Keys.BACKSPACE)  
        alert_name_input.send_keys(alert_name)
        open_tv_logger.info(f'Saved alert name to "{alert_name}"!')
      
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

    # get the indicator
    indicator = None
    if shorttitle == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif shorttitle == self.drawer_shorttitle:
      indicator = self.drawer_indicator

    try:
      if indicator != None: # that means that we've found our indicator
        eye = indicator.find_element(By.CSS_SELECTOR, 'div[data-name="legend-show-hide-action"]')
        status = 'Hidden' if 'disabled' in indicator.get_attribute('class') else 'Shown'
        
        if make_visible == False: 
          if status == 'Shown': # if status is "Hidden", that means that it is already hidden
            indicator.click()
            eye.click()
            open_tv_logger.info(f'Successfully changed the visibility of {shorttitle} to make it invisible!')
            return True
          if status == 'Hidden': # if status is "Hidden", that means that it is already hidden
            open_tv_logger.info(f'{shorttitle} indicator is already hidden. No need to change its visibility!')
            return True

        if make_visible == True: 
          if status == 'Hidden': # if status is "Shown", that means that it is already shown
            indicator.click()
            eye.click()
            open_tv_logger.info(f'Successfully changed the visibility of {shorttitle} to make it visible!')
            return True
          if status == 'Shown': # if status is "Hidden", that means that it is already hidden
            open_tv_logger.info(f'{shorttitle} indicator is already visible. No need to change its visibility!')
            return True
    except Exception as e:
      open_tv_logger.exception(f'Error ocurred when changing the visibility of {shorttitle} to make it {"visible" if make_visible else "invisible"}. Error: ')
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
      # find the indicator
      indicator = None
      if shorttitle == self.screener_shorttitle:
        indicator = self.screener_indicator
      elif shorttitle == self.drawer_shorttitle:
        indicator = self.drawer_indicator
      elif shorttitle == self.get_exits_shorttitle:
        indicator = self.get_exits_indicator

      # if there is no error
      if indicator.find_elements(By.CSS_SELECTOR, '.statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS') == []:
        open_tv_logger.info(f'There is no error in {shorttitle}!')
        return True
      
      open_tv_logger.error(f'There is an error in {shorttitle}.')
      return False
    except Exception as e:
      open_tv_logger.exception(f'Error ocurred when checking if {shorttitle} had an error. Error:')
      return False
    
  def delete_all_alerts(self):
    '''Waits for the alert sidebar to show up and deletes all the alerts if there are any. Then it waits a second.'''
    try:
      # wait for the alert sidebar to show up
      alert_sidebar = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.body-i8Od6xAB')))
      if not alert_sidebar:
        open_tv_logger.error('Alert sidebar not found. Cannot delete all alerts.')
        return False

      # Check if there already are no alerts
      sleep(3) #wait for the alert sidebar to load fully
      if self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5') == []:
        open_tv_logger.info('There are no alerts. No need to delete any alerts!')
        return True

      # click the 3 dots
      settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]')))
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))).click()
         
      # delete all alerts
      WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')))[-1].click() # in the dropdown which it opens, choose the "Remove all" option
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="yes"]'))).click() # click OK when the confirm dialog pops up

      sleep(1)
      if len(self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5')) == 0: # if there are no alerts visible (that means that the alerts have been deleted)
        open_tv_logger.info('All alerts have been sucessfully deleted!')
        return True
    except Exception as e:
      open_tv_logger.exception(f'Error happened somewhere when deleting all alerts. Failed to delete all alerts. Error:')
      return False
    
    return False

  def reupload_indicator(self, indicator, indicator_name, indicator_shorttitle):
    '''removes indicator and reuploads it again to the chart by clicking on the screener in the Favorites dropdown. It then waits for the indicator to show up on the chart and returns `True` if it does otherwise `False`.

    Don't remove the print statements. It seems like the code will only run with the print statements.'''
    val = False

    try:
      # click on the indicator
      indicator.click()

      # click on data-name="legend-delete-action" (a sub element under the indicator)
      delete_action = WebDriverWait(indicator, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-delete-action"]')))
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
            if indicator_shorttitle == self.get_exits_shorttitle:
              self.get_exits_indicator = self.get_indicator(indicator_shorttitle)
            break
        if val: # if the indicator is found on the chart, break the while loop
          open_tv_logger.info(f'{indicator_shorttitle} is on the chart after re-uploading it!')
          break
    except Exception as e:
      open_tv_logger.exception(f'An error occurred when re-uploading {indicator_shorttitle}. Could not reupload {indicator_shorttitle}. Error: ')
      return False

    return val

  def get_indicator(self, ind_shorttitle: str):
    '''Returns the indicator which has the same shorttitle as `ind_shorttitle`. If an indicator with the same shorttitle can't be found or an error occurrs, `None` will be returned'''
    try:
      indicator = None
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
    
  def current_chart_tframe(self):
    '''Returns the current chart's timeframe'''
    try:
      tf_button = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))
      return tf_button.get_attribute('aria-label')
    except Exception as e:
      open_tv_logger.exception(f'Failed to get the current chart timeframe. Error:')
      return ''
    
  def delete_get_exit_alert(self, alert_name):
    '''Deletes the alert which has its alert name as `alert_name` and returns `True` if the alert is deleted successfully and `False` if it is not deleted successfully.'''
    try:
      # wait for the alert sidebar to show up
      alert_sidebar = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.body-i8Od6xAB')))
      if not alert_sidebar:
        open_tv_logger.error('Alert sidebar not found. Cannot delete all alerts.')
        return False

      # Find the alert with the alert name
      xpath = f"//div[contains(@class, 'itemBody-ucBqatk5') and contains(@class, 'active-Bj96_lIl')][.//div[@data-name='alert-item-name' and text()='{alert_name}']]"
      alert = alert_sidebar[0].find_element(By.XPATH, xpath)

      # Delete it
      ActionChains(self.driver).move_to_element(alert).perform()
      remove_button = alert.find_element(By.CSS_SELECTOR, 'div[data-name="alert-delete-button"]')
      remove_button.click()

      # Wait for the confirmation popup to appear and click "Yes"
      popup = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]')))
      popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
    
    except Exception as e:
      open_tv_logger.exception(f'Failed to delete the {alert_name} alert. Error:')
      return False

  def alerts_sidebar_open(self):
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
      alerts = self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5')
      if not alerts: # if there are no alerts
        open_tv_logger.info('There are no alerts!')
        return True
      else:
        open_tv_logger.info('There are alerts!')
        return False
    except Exception as e:
      open_tv_logger.exception(f'Failed to check if there are no alerts. Error: ')
      return False