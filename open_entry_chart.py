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
    self.camera = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Take a snapshot']/div[@id='header-toolbar-screenshot']")))

  def change_indicator_settings(self, _type, direction, entry, tp, sl, time_of_entry=1):
    # get the 1st indicator on the top of the chart
    indicators = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')

    # change the settings
    while True:
      try:
        # double click on the indicator so that the settings can open 
        ActionChains(self.driver).move_to_element(indicators[0]).perform()
        ActionChains(self.driver).double_click(indicators[0]).perform()
        settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
        break
      except Exception as e:
        print(f'error in {__file__}: \n', e)
        continue
    inputs = settings.find_elements(By.CSS_SELECTOR, '.cell-tBgV1m0B input')

    for i in range(len(inputs)):
      val = 30
      if i == 0:
        val = _type
      if i == 1:
        val = entry
      elif i == 2:
        val = tp
      elif i == 3:
        val = sl
      elif i == 4:
        val = direction
      elif i == 6 and _type == 'Exit':
        val = time_of_entry

      ActionChains(self.driver).key_down(Keys.CONTROL, inputs[i]).send_keys('a').perform()
      inputs[i].send_keys(Keys.DELETE)
      inputs[i].send_keys(val)

    # click on submit
    self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()

    # wait for the indicator to fully load so that it can take a snapshot of the new entry, sl & tp
    while True:
      class_attr = indicators[0].get_attribute('class')
      if 'loading' not in class_attr:
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
    # copy the link of the chart
    self.camera.click()
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