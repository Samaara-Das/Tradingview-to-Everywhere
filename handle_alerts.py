'''
This handles getting the alert and the alert message, removing it from the log, restarting inactive alerts and posting entry snapshots everywhere.
'''

from resources.utils import Utils
import logger_setup
import open_entry_chart
from datetime import datetime
from resources.symbol_settings import symbol_category
import send_to_socials.discord as discord
import database.nk_db as nk_db
import database.local_db as local_db
from time import sleep, time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from json import loads

# Set up logger for this file
alert_data_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

# class
class Alerts:

  def __init__(self, drawer_shorttitle, screener_shortitle, driver, chart_timeframe, interval_seconds) -> None:
    self.driver = driver
    self.local_db = local_db.Database('')
    self.nk_db = nk_db.Post()
    self.chart = open_entry_chart.OpenChart(self.driver)
    self.discord = discord.Discord()
    self.drawer_shorttitle = drawer_shorttitle
    self.utils = Utils()
    self.screener_shortitle = screener_shortitle
    self.chart_timeframe = chart_timeframe
    self.interval_seconds = interval_seconds
    self.last_run = time()
    
  def post(self, msg, screener_visibility):
    '''This goes through every entry in `msg` and takes a snapshot of those entries and posts them to Nk uncle's database, our remote database & Discord'''
    try:
      if not screener_visibility(False, self.screener_shortitle): # hide the screener indicator with the passed in function
        alert_data_logger.warning('Failed to hide the screener indicator but still continuing to post about entries')
    
      for key, value in msg.items(): # go over every json field in this specific alert message
        try:
          # get all the data from the message
          timeframe = value['timeframe']
          entry_time = int(value['entryTime'].replace(',', ''))
          entry_price = value['entryPrice']
          formatted_time = datetime.fromtimestamp(float(entry_time)/1000).strftime('%Y-%m-%d %H:%M') # divide entry_time by 1000 because the function accepts only seconds not milliseconds
          sl_price = float(value['slPrice'])
          tp1_price = float(value['tp1Price'])
          tp2_price = float(value['tp2Price'])
          tp3_price = float(value['tp3Price'])
          direction = str(value['direction'])

          # go to that specific entry's symbol and its timeframe. Then it inputs all the entry info into the Trade Drawer indicator
          if not self.chart.change_symbol(key):
            alert_data_logger.error(f'Error in changing the symbol to {key}. Going to next symbol.')
            continue
          if not self.chart.change_tframe(self.chart_timeframe):
            alert_data_logger.error(f'Error in changing the timeframe to {timeframe}. Going to next symbol.')
            continue
          if not self.chart.change_indicator_settings(self.drawer_shorttitle, entry_time, entry_price, sl_price, tp1_price, tp2_price, tp3_price):
            alert_data_logger.error(f'Error in changing the Trade Drawer indicator\'s settings. Going to next symbol.')
            continue

          # Take a snapshot of it and send it to social media
          if not self.send_everywhere(direction=direction, key=key, timeframe=timeframe, entry_price=entry_price, tp1_price=tp1_price, tp2_price=tp2_price, tp3_price=tp3_price, sl_price=sl_price, entry_time=entry_time, formatted_time=formatted_time, value=value):
            alert_data_logger.error(f'Error in sending the entry to all platforms. Going to next symbol.')
            continue

        except Exception as e:
          alert_data_logger.exception(f'Error in posting an entry. Continuing to next entry. Error:')
          continue
    
    except Exception as e:
      alert_data_logger.exception('Error in posting an entry. Continuing to next entry. Error:')

  def send_everywhere(self, **kwargs):
    '''
    This sends posts to Discord, my database and Nk uncle's API.

    Args:
        kwargs (dict): A dictionary of arguments containing:
            direction (str): Direction of the trade (buy/sell).
            key (str): Symbol of the trade.
            timeframe (str): Timeframe of the trade.
            entry_price (float): Entry price of the trade.
            tp1_price (float): First take profit price.
            tp2_price (float): Second take profit price.
            tp3_price (float): Third take profit price.
            sl_price (float): Stop loss price.
            entry_time (int): Unix timestamp of the entry time.
            formatted_time (str): Formatted entry time.
            value (dict): Additional information for Nk uncle's API.
    '''
    try:
        # Extracting necessary parameters from kwargs
        direction = kwargs.get('direction')
        key = kwargs.get('key')
        timeframe = kwargs.get('timeframe')
        entry_price = kwargs.get('entry_price')
        tp1_price = kwargs.get('tp1_price')
        tp2_price = kwargs.get('tp2_price')
        tp3_price = kwargs.get('tp3_price')
        sl_price = kwargs.get('sl_price')
        entry_time = kwargs.get('entry_time')
        formatted_time = kwargs.get('formatted_time')
        value = kwargs.get('value')

        png_link, tv_link = '', ''
        links = self.chart.save_chart_img() 
        if links:
          png_link, tv_link = links['png'], links['tv'] 
        category = symbol_category(key)

        # Discord
        content = f"{direction} in {key} at {entry_price}. TP1: {tp1_price} TP2: {tp2_price} TP3: {tp3_price} SL: {sl_price} Link: {png_link}"
        self.discord.send_to_entry_channel(category, content) 

        # My database
        self.local_db.add_doc({"direction": direction, "symbol": key, "timeframe": timeframe, "entryPrice": entry_price, "tp1Price": tp1_price, "tp2Price": tp2_price, "tp3Price": tp3_price, "slPrice": sl_price, "tvEntrySnapshot": tv_link, "pngEntrySnapshot": png_link, "content": content, "unixTime": entry_time, "category": category, "isSlHit": False, "isTp1Hit": False, "isTp2Hit": False, "isTp3Hit": False, "tvExitSnapshot": '', "pngExitSnapshot": ''}, "Entries")
        
        # Nk uncle's server
        self.nk_db.post_to_url({"type": value['type'], "direction": direction, "symbol": key, "tframe": timeframe, "entry": entry_price, "tp1": tp1_price, "tp2": tp2_price, "tp3": tp3_price, "sl": sl_price, "chart_link": png_link, "content": content, "date": formatted_time, "symbol_type": category, "exit_msg": ''})
        
        # Log success
        alert_data_logger.info(f"Successfully sent entry data to all platforms for symbol {key}.")
        return True
    except Exception as e:
        alert_data_logger.error(f"Error sending entry data: {e}")
        return False

  def post_entries(self, screener_visibility):
    '''This goes through all the alerts in the Alerts log and posts each entry that came until all the alerts have been read.'''
    try:
      self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open
      alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
      while alert_boxes:
        alert = self.get_alert()
        self.post(alert, screener_visibility)
        self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open
        alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
    except TimeoutException:
      alert_data_logger.warning('Timeout exception occurred. Assuming that there are no alert boxes.')

  def restart_inactive_alerts(self):
    '''Restarts all the inactive alerts by going to the settings and clicking on "Restart all inactive". Then it will click "Yes" on the popup which comes to confirm the restarting of the alerts.'''
    try:
      # Make sure that the Alerts tab is open
      self.utils.open_alert_tab(self.driver)

      # click the 3 dots
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))).click()
      
      # wait for the dropdown to show up
      dropdown = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]')))
      
      # check if the "Show Alerts" section is minimised. if it is, maximise it
      show_all_section = dropdown.find_element(By.CSS_SELECTOR, 'div[class="section-xZRtm41u summary-ynHBVe1n"]')
      maximized = True if show_all_section.get_attribute('data-open') == 'true' else False
      if not maximized:
        show_all_section.click()
        alert_data_logger.info('Maximized the "Show Alerts" section')

      # then check if the "All" option is selected. if it is not, select it
      all_option = dropdown.find_element(By.CSS_SELECTOR, 'div[class="item-xZRtm41u item-jFqVJoPk"]')
      if not all_option.find_element(By.TAG_NAME, 'input').is_selected():
        all_option.click()
        alert_data_logger.info('Selected the "All" option')

      # then click on "Restart all inactive"
      dropdown_button = dropdown.find_element(By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')
      if dropdown_button.text == 'Restart all inactive':
        dropdown_button.click()
        alert_data_logger.info('Clicked on "Restart all inactive"')

        # click Yes when the popup comes
        popup = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]')))
        popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
        alert_data_logger.info('Restarting all inactive alerts!')

      sleep(1)
      return True
    except Exception as e:
      alert_data_logger.exception('Error occurred when restarting the inactive alerts. Error:')
      return False

  def get_alert(self):
    '''Whenever it sees an alert in the Logs tab, the alert gets deleted from the log and its message gets returned'''
    try:
      alert_box, alert_msg = self.get_alert_box_and_msg()
      if alert_box and alert_msg:
        if self.remove_alert(alert_box):
          return loads(alert_msg) if alert_msg != None else loads('{}')# the alert message is jsonified
        
    except StaleElementReferenceException:
      alert_data_logger.error('StaleElementReferenceException while reading the alert. Trying again to get alert...')
      alert_box, alert_msg = self.get_alert_box_and_msg()
      if alert_box and alert_msg:
        if self.remove_alert(alert_box):
          return loads(alert_msg) if alert_msg != None else loads('{}')# the alert message is jsonified
    
    except Exception as e:
      alert_data_logger.exception('Error in reading the alert. Error:')
      return loads('{}')

  def get_exit_alert(self, alert_name, symbol):
    '''This waits for 20 secs for an alert from the Get Exits indicator to come and returns it's message'''
    start_time = time()
    while True:
      # only wait for an alert for a couple seconds
      current_time = time()
      if current_time - start_time > 20: 
        return loads('{}')  

      try:
        alert_msg = self.get_exit_alert_msg(alert_name, symbol)
        if alert_msg != None:
          return loads(alert_msg) # the alert message is jsonified
        else:
          continue
      
      except Exception as e:
        alert_data_logger.exception('Error in reading the alert. Error:')

  def get_exit_alert_msg(self, alert_name, symbol):
    '''Returns the alert message that comes from the alert called `alert_name` and the symbol `symbol`. If there is no alert, it waits for one. Also, it restarts all the inactive alerts periodically. If something goes wrong, `None` gets returned'''
    try:
      # restart all the inactive alerts every INTERVAL_MINUTES minutes (this is also done in get_alert_data.py in the method get_alert_box_and_msg())
      if time() - self.last_run > self.interval_seconds:
        self.restart_inactive_alerts()
        self.last_run = time()

      self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open

      alert_box = self.driver.find_element(By.CSS_SELECTOR, 'div[class="widgetbar-page active"] div[data-name="alert-log-item"]')
      first_alert_name = alert_box.find_element(By.CSS_SELECTOR, 'div[class="name-PQUvhamm"]').text
      first_alert_msg = alert_box.find_element(By.CSS_SELECTOR, 'div[class="message-PQUvhamm"]').text
      first_alert_symbol = alert_box.find_element(By.CSS_SELECTOR, 'span[class="attribute-PQUvhamm ticker-PQUvhamm"]').text
      if first_alert_name == alert_name and symbol in first_alert_symbol:
        return first_alert_msg
      return None
    except TimeoutException:
      alert_data_logger.error('TimeoutException occured while waiting for a Get Exit alert.')
      return None
    except Exception as e:
      alert_data_logger.exception('Error in getting the Get Exit\'s alert message. Error:')
      return None

  def get_alert_box_and_msg(self):
    '''Returns the last alert box and its message if there is an alert. If there is no alert, it waits for one. Also, it restarts all the inactive alerts periodically. If something goes wrong, `None, None` gets returned'''
    try:
      # restart all the inactive alerts every INTERVAL_MINUTES minutes (this is also done in get_alert_data.py in the method get_alert_box_and_msg())
      if time() - self.last_run > self.interval_seconds:
        self.restart_inactive_alerts()
        self.last_run = time()

      self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open
      alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
      if alert_boxes:
        alert_box = alert_boxes[-1] # take the last alert (the oldest one)
        alert_msg = alert_box.find_element(By.CSS_SELECTOR, 'div[class="message-PQUvhamm"]').text 
        if not alert_box.is_displayed() and not self.scroll_to_alert(alert_box):
          alert_data_logger.error('Failed to scroll to alert')
          return loads('{}'), loads('{}')
        return alert_box, alert_msg
      return loads('{}'), loads('{}')
    except TimeoutException:
      alert_data_logger.error('TimeoutException occured while waiting for an alert.')
      return loads('{}'), loads('{}')
    except Exception as e:
      alert_data_logger.exception('Error in getting the alert box and message. Error:')
      return loads('{}'), loads('{}')
      
  def remove_alert(self, alert_box):
    '''Removes the alert from the Alert log'''
    try:
      self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open
      ActionChains(self.driver).move_to_element(alert_box).perform()
      remove_button = alert_box.find_element(By.CSS_SELECTOR, 'div[data-name="event-delete-button"]')
      remove_button.click()
      return True
    except Exception as e:
      alert_data_logger.exception('Error in removing the alert from the Alert log. Error:')
      return False

  def scroll_to_alert(self, alert):
    '''This scrolls to the given alert'''
    try:
      self.driver.execute_script("arguments[0].scrollIntoView();", alert)
      return True
    except Exception as e:
      alert_data_logger.exception('Error in scrolling to the alert. Error:')
      return False