'''
this opens up a new tab in the browser and sets it up for taking snapshots of the entries/exits
'''


# import modules
from time import sleep
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# class
class OpenChart:

  def __init__(self, driver) -> None:
    self.driver = driver

  def open_new_tab(self):
    # Opening a duplicate tab
    self.driver.execute_script('''window.open("{}");'''.format(self.driver.current_url))  
    self.new_tab_handle = self.driver.window_handles[1]

  def change_indicator_settings(self, entry, tp, sl):
    # double click on the indicator
    indicators = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')

    ActionChains(self.driver).move_to_element(indicators[0]).perform()
    ActionChains(self.driver).double_click(indicators[0]).perform()

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

  def change_tframe(self, timeframe):
    # click on the dropdown and choose from the dropdown options and click on the one which matches the timeframe
    tf_dropdown = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))
    tf_dropdown.click()
    options = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div')))
    options = options.find_elements(By.CSS_SELECTOR, 'div > div')

    for option in options:
      if option.get_attribute('data-value') == timeframe:
        option.click()
        break
                                               
