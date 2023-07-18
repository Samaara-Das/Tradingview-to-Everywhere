'''
this opens up a new tab in the browser and sets it up for taking snapshots of the entries/exits
'''


# import modules
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# class
class OpenChart:

  def __init__(self, driver) -> None:
    self.driver = driver
    self.timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '3h', '4h', 'D', 'W', 'M']
    self.old_tab_handle = self.driver.window_handles[0]

  def open_new_tab(self):
    # Opening a duplicate tab
    self.driver.execute_script('''window.open("{}");'''.format(self.driver.current_url))  
    self.new_tab_handle = self.driver.window_handles[1]

  def change_symbol(self, symbol):
    # only search for a specific symbol if the current symbol is different from that symbol
    symbol_search = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-symbol-search"]')))
    if symbol_search.find_element(By.CSS_SELECTOR, 'div').text == symbol:
      return
    
    # click on Symbol Search and search for a specific symbol and hit ENTER
    symbol_search.click()
    search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div[2]/div[1]/input')
    search_input.send_keys(symbol)
    search_input.send_keys(Keys.ENTER)

  def alert_tf_converter(self, timeframe):
    # this returns the timeframe equivalent for the timeframe we get in the alert

    if timeframe == '1':
      return '1m'
    elif timeframe == '3':
      return '3m'
    elif timeframe == '5':
      return '5m'
    elif timeframe == '15':
      return '15m'
    elif timeframe == '30':
      return '30m'
    elif timeframe == '60':
      return '1h'
    elif timeframe == '120':
      return '2h'
    elif timeframe == '180':
      return '3h'
    elif timeframe == '240':
      return '4h'
    elif timeframe == '1D':
      return 'D'
    elif timeframe == '1M':
      return 'M'

  def change_tframe(self, timeframe):
    # see if the current timeframe is the same as the one we want, if so, do nothing
    tf_dropdown = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))

    if tf_dropdown.text == self.alert_tf_converter(timeframe):
      return
    
    # choose from the dropdown options and click on the one which matches the timeframe
    tf_dropdown.click()
    options = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div')))
    options = options.find_elements(By.CSS_SELECTOR, 'div > div')

    for option in options:
      if option.get_attribute('data-value') == timeframe:
        option.click()
        break
                                               
  def switch_to_old_tab(self):
    self.driver.switch_to.window(self.old_tab_handle)

  def switch_to_new_tab(self):
    self.driver.switch_to.window(self.new_tab_handle)
    
