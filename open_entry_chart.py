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
    self.entry = 0
    self.tp = 0
    self.sl = 0
    self.symbol = ''
    self.timeframe = ''
    self.old_tab_handle = self.driver.window_handles[0]

  def open_new_tab(self):
    # Opening a duplicate tab
    self.driver.execute_script('''window.open("{}");'''.format(self.driver.current_url))  
    self.new_tab_handle = self.driver.window_handles[1]

  def change_symbol(self, symbol):
    # click on Symbol Search and search for a specific symbol and hit ENTER
    symbol_search = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-symbol-search"]')))
    symbol_search.click()
    search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div[2]/div[1]/input')
    search_input.send_keys(symbol)
    search_input.send_keys(Keys.ENTER)

  def change_tframe(self, timeframe):
    # click on the timeframe and choose from the dropdown
    tf_dropdown = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))
    tf_dropdown.click()
    

  def switch_to_old_tab(self):
    self.driver.switch_to.window(self.old_tab_handle)

  def switch_to_new_tab(self):
    self.driver.switch_to.window(self.new_tab_handle)
    
