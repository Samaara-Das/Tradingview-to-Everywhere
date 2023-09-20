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
SYMBOL_INPUTS = 16

CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
# CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'


# class
class Browser:

  def __init__(self, keep_open: bool, tabs: int) -> None:
    chrome_options = Options() 
    chrome_options.add_experimental_option("detach", keep_open)

    chrome_options.add_argument('--profile-directory=Profile 2')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    self.tabs = tabs
    self.open_chart = OpenChart(self.driver)

  def open_page(self, url: str):
    self.driver.get(url)
    self.driver.maximize_window()
  
  def close_page(self):
    print("shutting down tab 💤")
    self.driver.close()

  def open_tv(self):
    # open tradingview
    self.open_page('https://www.tradingview.com/chart')

    # change to the screener layout (if we are on any other layout)
    self.change_layout()

    # delete all alerts
    self.delete_alerts()

    # set the timeframe to 1m so that when the alert for the screener is set up, an error won't happen
    # 1min is not the timeframe that entries are happening on. that timeframe is on pinescript
    self.open_chart.change_tframe('1')

    # make the screener visible
    self.screener_visibility(True)

    #give it some time to delete all those alerts
    sleep(2) 
    
    tabs = self.tabs-1

    for i in range(tabs):
      self.driver.execute_script("window.open('https://www.tradingview.com/chart','_blank')")

  def set_alerts_and_settings(self):
    '''
    all the symbols together from symbols_settings.py must cover each tab's need for 8 symbols.
    the value of (total symbols / total tabs) must be equal to/more than 8
    '''

    all_symbols = []
    for symbols in main_symbols:
      _list = list(symbols['symbols'])
      all_symbols.extend(_list)

    for tab in range(self.tabs):
      # switch tab
      self.driver.switch_to.window(self.driver.window_handles[tab])

      # set the timeframe to 1min so that when the alert for the screener is set up, an error won't happen
      self.open_chart.change_tframe('1')

      # change settings this particular symbol
      self.change_settings(all_symbols)

      # remove the first 8 symbols
      if len(all_symbols) > SYMBOL_INPUTS:
        all_symbols = all_symbols[SYMBOL_INPUTS:]

      # setup alert for this particular symbol
      self.set_alerts(tab)

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
    self.open_chart.change_symbol(symbols_list[0])

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

  def set_alerts(self, tab):
    tab_no = tab + 1

    # make the screener indicator visible
    self.screener_visibility(True)

    # wait for the screener indicator to fully load
    self.is_eye_loaded()

    # check if the screener indicator has no error
    if not self.is_indicator_loaded(check_signal_ind=False):
      print('screener indicator had an error. Could not set an alert for this tab. exiting method')
      return

    # hide the screener indicator by clicking the eye
    self.screener_visibility(False)

    while True:
      try:
        # wait for the + button to be clickable
        plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
        break
      except Exception as e:
        print(f'error in {__file__}: \n{e}')
        continue


    # wait for the set alerts popup box
    while True:
      try:
        # click on the + button
        plus_button.click()
        set_alerts_popup = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
        break
      except Exception as e:
        print(f'error in {__file__}: \n{e}')
        continue
    
    # click the dropdown and choose the screener
    try:
      set_alerts_popup.find_element(By.CSS_SELECTOR, 'span[data-name="main-series-select"]').click()
    except Exception as e:
      print(f'from {__file__}: \ncouldn\'t find screener dropdown when making alert \n{e}')

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
    sleep(1)
    while True:
      try:
        indicator = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')[1]
        if 'loading' not in indicator.get_attribute('class'):
          break   
      except Exception as e:
        print(f'error in {__file__}: \n{e}')
        continue

  def screener_visibility(self, make_visible: bool):
    # click on the screener indicator to show the eye symbol
    indicator = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')[1]
    while True:
      try:
        indicator.click()
        break
      except Exception as e:
        print(f'error in {__file__}: \n{e}')
        continue
    
    class_attr = indicator.get_attribute('class')
    eye = indicator.find_element(By.CSS_SELECTOR, 'div[data-name="legend-show-hide-action"]')

    # if we want to make it invisible
    if make_visible == False:
      # check if it is visible to make it invisible. if it is not visible, then no need to click on the eye
      if 'disabled' not in class_attr:
        eye.click()
    
    # if we want to make it visible
    else:
      # check if it is invisible to make it visible. if it is not invisible, then no need to click on the eye 
      if 'disabled' in class_attr:
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



