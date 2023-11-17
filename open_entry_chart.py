'''
this sets up the tradingview tab for taking snapshots of the entries/exits.
this:
1. changes the settings of the signal indicator
2. change the symbol of the chart
3. change the timeframe of the chart
4. opens the image of the chart in a new tab, copies the url and closes the tab
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
    
  def change_indicator_settings(self, drawer_indicator, entry_time, entry_price, sl_price, tp1_price, tp2_price, tp3_price):
    # double click on the indicator so that the settings can open 
    ActionChains(self.driver).move_to_element(drawer_indicator).perform()
    ActionChains(self.driver).double_click(drawer_indicator).perform()
    settings = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
    inputs = settings.find_elements(By.CSS_SELECTOR, '.cell-tBgV1m0B input')

    # fill up the settings
    for i in range(len(inputs)):
      val = 0
      if i == 0:
        val = entry_time
      elif i == 1:
        val = entry_price
      elif i == 2:
        val = sl_price
      elif i == 3:
        val = tp1_price
      elif i == 4:
        val = tp2_price
      elif i == 5:
        val = tp3_price

      ActionChains(self.driver).key_down(Keys.CONTROL, inputs[i]).send_keys('a').perform()
      inputs[i].send_keys(Keys.DELETE)
      inputs[i].send_keys(val)

    # click on submit
    self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()

    # wait for the indicator to fully load so that it can take a snapshot of the new entry, sl & tp
    sleep(1) 
    while True:
      class_attr = drawer_indicator.get_attribute('class')
      if 'Loading' not in class_attr:
        break
      else:
        continue
    sleep(1)

  def change_symbol(self, symbol):
    # only search for a specific symbol if the current symbol is different from that symbol
    symbol_search = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-symbol-search"]')))
    if not symbol_search.find_element(By.CSS_SELECTOR, 'div').text == symbol:
    # click on Symbol Search and search for a specific symbol and hit ENTER
      symbol_search.click()
      search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div[2]/div[1]/input')
      search_input.send_keys(symbol)
      search_input.send_keys(Keys.ENTER)

  def change_tframe(self, timeframe):
    '''`timeframe` is supposed to be the value of the data-value attribute of the timeframe dropdown options in Tradingview.'''
    # click on the dropdown and choose from the dropdown options and click on the one which matches the timeframe
    tf_dropdown = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))
    tf_dropdown.click()
    options = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div')))
    options = options.find_elements(By.CSS_SELECTOR, 'div > div')

    for option in options:
      if option.get_attribute('data-value') == timeframe:
        option.click()
        break
                                               
  def save_chart_img(self):
    camera = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Take a snapshot']/div[@id='header-toolbar-screenshot']")))

    # copy the link of the chart
    camera.click()
    open_in_new_tab = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[5]')
    open_in_new_tab.click()

    # get the url of the newly opened tab after it has fully loaded
    self.driver.switch_to.window(self.driver.window_handles[-1])
    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img[class="tv-snapshot-image"]')))
    url = self.driver.current_url

    # close the new tab 
    self.driver.close()

    # switch back to the original tab
    self.driver.switch_to.window(self.driver.window_handles[0])

    return url