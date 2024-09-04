'''
this can change the Trade Drawer's settings, change the chart's symbol and timeframe and take a snapshot of the chart.
'''

# import modules
import logger_setup
from time import sleep, time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Set up logger for this file
entry_chart_logger = logger_setup.setup_logger(__name__, logger_setup.DEBUG)

# class
class OpenChart:

  def __init__(self, driver) -> None:
    self.driver = driver
    
  def change_indicator_settings(self, drawer_shorttitle, entry_time, entry_price, sl_price, tp1_price, tp2_price, tp3_price):
    try:
      # double click on the indicator so that the settings can open 
      i = 1
      while i <= 3:
        try:
          drawer_indicator = self.get_indicator(drawer_shorttitle)
          ActionChains(self.driver).move_to_element(drawer_indicator).perform()
          ActionChains(self.driver).double_click(drawer_indicator).perform()
          settings = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="indicator-properties-dialog"]')))
          break
        except Exception as e:
          entry_chart_logger.exception('Failed to open the Trade Drawer\'s settings. Error:')
          i += 1
          if i == 4:
            entry_chart_logger.error('Trade Drawer indicator\'s settings failed to open. Could not change the settings. Exiting function.')
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

      entry_chart_logger.info(f'Trade Drawer\'s settings changed. Inputs: entry_time - {entry_time}, entry_price - {entry_price}, sl_price - {sl_price}, tp1_price - {tp1_price}, tp2_price - {tp2_price}, tp3_price - {tp3_price}')

      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()

      # wait for the indicator to fully load so that it can take a snapshot of the new entry, sl & tp
      start_time = time()
      timeout = 15  # 15 seconds
      check = False
      sleep(2)
      while time() - start_time <= timeout:
        class_attr = drawer_indicator.get_attribute('class')
        if 'Loading' not in class_attr:
          check = True
          entry_chart_logger.info('Trade indicator fully loaded!')
          return True
        else:
          continue
      if check == False:
        entry_chart_logger.error('Trade indicator did not fully load.')
        return False
    except Exception as e:
      entry_chart_logger.exception('Failed to change the Trade Drawer\'s settings. Error:')
      return False

  def change_get_exit_settings(self, get_exits_shorttitle, entry_time, entry_price, entry_type, sl_price, tp1_price, tp2_price, tp3_price):
    '''This double clicks on the Get Exits indicator to open its settings and changes its inputs'''
    try:
      # double click on the indicator so that the settings can open 
      i = 1
      while i <= 3:
        try:
          get_exits_indicator = self.get_indicator(get_exits_shorttitle)
          ActionChains(self.driver).move_to_element(get_exits_indicator).perform()
          ActionChains(self.driver).double_click(get_exits_indicator).perform()
          settings = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="indicator-properties-dialog"]')))
          break
        except Exception as e:
          entry_chart_logger.exception('Failed to open the Trade Drawer\'s settings. Error:')
          i += 1
          if i == 4:
            entry_chart_logger.error('Trade Drawer indicator\'s settings failed to open. Could not change the settings. Exiting function.')
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

      entry_chart_logger.info(f'Get Exits\'s settings changed. Inputs: entry_time - {entry_time}, entry_price - {entry_price}, entry_type - {entry_type}, sl_price - {sl_price}, tp1_price - {tp1_price}, tp2_price - {tp2_price}, tp3_price - {tp3_price}')

      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
      return True
    except Exception as e:
      entry_chart_logger.exception('Failed to change the Get Exits\'s settings. Error:')
      return False

  def change_symbol(self, symbol):
    '''This changes the chart's symbol to `symbol` if it is any other symbol. Then it waits for 1.5 secs for the chart to load'''
    try:
      no_exchange_symbol = symbol.split(':')[-1] if ':' in symbol else symbol # get the symbol without the exchange name (if there is an exchange name)
      symbol_search = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"]')))
      if not symbol_search.find_element(By.CSS_SELECTOR, 'div').text == no_exchange_symbol: # only search for a specific symbol if the current symbol is different from that symbol
        # click on Symbol Search and search for a specific symbol and hit ENTER
        symbol_search.click()
        search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div[2]/div[1]/input')
        ActionChains(self.driver).key_down(Keys.CONTROL, search_input).send_keys('a').perform()
        search_input.send_keys(Keys.DELETE)
        search_input.send_keys(symbol)
        search_input.send_keys(Keys.ENTER)
        entry_chart_logger.info(f'Entered symbol {symbol}') 
        WebDriverWait(self.driver, 5).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"] div'), no_exchange_symbol))
        sleep(1.5) # wait for the chart to load
        return True
      else:
        entry_chart_logger.info(f'The current symbol is the same as {no_exchange_symbol}. There is no need to change the symbol!')
        return True
    except Exception as e:
      entry_chart_logger.exception(f'Failed to change the symbol of the chart. Error: ')
      return False

  def change_tframe(self, timeframe):
    '''Changes the timeframe of the chart to `timeframe`'''
    try:
      # click on the timeframe dropdown and choose from the dropdown options and click on the one which matches the timeframe
      tf_button = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))

      if tf_button.get_attribute('aria-label') != timeframe: # if the chart's timeframe is different, change it to the desired timeframe
        tf_button.click()
        options = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="dropdown-S_1OCXUK"]')))
        options = options.find_elements(By.CSS_SELECTOR, 'div[class="accessible-NQERJsv9 menuItem-RmqZNwwp item-jFqVJoPk"]')

        for option in options:
          if option.find_element(By.CSS_SELECTOR, 'span[class="label-jFqVJoPk"]').text == timeframe:
            option.click()
            entry_chart_logger.info(f'Successfully changed the timeframe to {timeframe}!')
            return True
      elif tf_button.get_attribute('aria-label') == timeframe: # if the chart's timeframe is already the desired timeframe
        entry_chart_logger.info('No need to change the timeframe as the current chart is already on that timeframe!')
        return True
      
      return False
    except Exception as e:
      entry_chart_logger.exception(f'Failed to change the timeframe of the chart to {timeframe}. Error:')
      return False

  def get_exit_snapshot(self, get_exits_shorttitle):
    '''This waits for the indicator to load, take's a snapshot of the chart and returns links '''
    try:
      # wait for the indicator to fully load so that a snapshot can be taken
      start_time = time()
      timeout = 15  # 15 seconds
      check = False
      sleep(2)
      while time() - start_time <= timeout:
        get_exits_indicator = self.get_indicator(get_exits_shorttitle)
        class_attr = get_exits_indicator.get_attribute('class')
        if 'Loading' not in class_attr:
          check = True
          entry_chart_logger.info('Get Exits indicator fully loaded!')
          break
        else:
          continue
      if check == False:
        entry_chart_logger.error('Get Exits indicator did not fully load.')
        return False

      # Take a snapshot of the exit
      return self.save_chart_img() 
    except Exception as e:
      entry_chart_logger.exception('Error in posting an entry. Error:')
                                            
  def save_chart_img(self):
    '''Clicks on the camera icon to take a snapshot of the chart and opens it in a new tab. The link of the tab and image are returned in a dictionary. If an error occurs, an empty string is returned.
    
    Returns
    - Dictionary with keys 'png' and 'tv' if successful, otherwise an empty dictionary.
    '''
    png_link = ''
    tv_link = ''
    try:
      camera = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Take a snapshot']/div[@id='header-toolbar-screenshot']")))

      # copy the link of the chart
      camera.click()
      open_in_new_tab = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[5]')
      open_in_new_tab.click()
      entry_chart_logger.info(f'Took a snapshot and opened it in new tab.')

      # get the url of the newly opened tab after it has fully loaded
      self.driver.switch_to.window(self.driver.window_handles[-1])
      img_element = WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img.tv-snapshot-image')))
        
      # Get the link of the tab and src attribute value of the image
      tv_link = self.driver.current_url
      png_link = img_element.get_attribute('src')
      entry_chart_logger.info(f'Got link of image and tab!')

      # close the new tab 
      self.driver.close()

      # switch back to the original tab
      self.driver.switch_to.window(self.driver.window_handles[0])

    except Exception as e:
      entry_chart_logger.exception('Failed to save the chart image. Attempting to close new tab if open. Error:')
      # Close the tab that was opened for a snapshot
      if len(self.driver.window_handles) == 2:
        for handle in self.driver.window_handles:
          self.driver.switch_to.window(handle)
          if 'Image' in self.driver.title:
            entry_chart_logger.info(f'Closing the snapshot tab')
            self.driver.close()
            break

      self.driver.switch_to.window(self.driver.window_handles[0])
      return {}
    
    return {'png': png_link, 'tv': tv_link}
  
  def get_indicator(self, ind_shorttitle: str):
    '''Returns the indicator which has the same shorttitle as `ind_shorttitle`. If an indicator with the same shorttitle can't be found or an error occurrs, `None` will be returned'''
    try:
      indicator = None
      wait = WebDriverWait(self.driver, 15)
      indicators = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')))
      
      for ind in indicators: 
        indicator_name = ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text
        if indicator_name == ind_shorttitle: # finding the indicator
          entry_chart_logger.info(f'Found indicator {ind_shorttitle}!')
          indicator = ind
          break
    except Exception as e:
      entry_chart_logger.exception(f'Failed to find indicator {ind_shorttitle}. Error:')
      return None

    return indicator