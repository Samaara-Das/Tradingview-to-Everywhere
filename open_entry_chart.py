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

  def change_symbol_tframe(self, symbol):
    # self.switch_to_new_tab()
    self.driver.find_element(By.CLASS_NAME, 'input-3lfOzLDc').send_keys(Keys.CONTROL + "a")
    self.driver.find_element(By.CLASS_NAME, 'input-3lfOzLDc').send_keys(Keys.DELETE)
    self.driver.find_element(By.CLASS_NAME, 'input-3lfOzLDc').send_keys(symbol)

  def switch_to_old_tab(self):
    self.driver.switch_to.window(self.old_tab_handle)

  def switch_to_new_tab(self):
    self.driver.switch_to.window(self.new_tab_handle)
    
