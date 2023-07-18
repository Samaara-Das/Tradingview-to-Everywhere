'''
this opens up a new tab in the browser and sets it up for taking snapshots of the entries/exits
'''


# import modules
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# class
class OpenChart:

  def __init__(self, driver, entry, tp, sl, symbol, timeframe) -> None:
    self.driver = driver
    self.entry = entry
    self.tp = tp
    self.sl = sl
    self.symbol = symbol
    self.timeframe = timeframe
    self.old_tab_handle = self.driver.window_handles[0]

  def open_new_tab(self):
    # Opening a duplicate tab
    self.driver.execute_script('''window.open("{}");'''.format(self.driver.current_url))  
    self.new_tab_handle = self.driver.window_handles[1]

  def set_up_new_tab(self):
    # click on the trash icon
    locator = (By.XPATH, '//*[@id="drawing-toolbar"]/div/div/div/div/div[4]/div/div/div/button')
    button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(locator))
    button.click()


  def switch_to_old_tab(self):
    self.driver.switch_to.window(self.old_tab_handle)

  def switch_to_new_tab(self):
    self.driver.switch_to.window(self.new_tab_handle)
    
