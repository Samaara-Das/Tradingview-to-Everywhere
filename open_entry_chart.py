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
    # add the inidcator onto the chart (the one which will draw entry/tp/sl lines)
    self.add_indicator()

  def add_indicator(self):
    while True:
      try:
        arrow_btn = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Indicators, Metrics & Strategies']")))
        print('⬇️ clicked on indicator button', arrow_btn.tagname)
        arrow_btn.click()
        break
      except:
        # print('couldnt clcik on indicator button')
        continue

  def switch_to_old_tab(self):
    self.driver.switch_to.window(self.old_tab_handle)

  def switch_to_new_tab(self):
    self.driver.switch_to.window(self.new_tab_handle)
    
