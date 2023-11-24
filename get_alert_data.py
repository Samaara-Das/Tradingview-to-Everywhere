'''
This module does the following:
1. clears the alert log
2. gets all the alerts from the alert log
3. reads the alert messages and does certain actions after reading them
4. sends content to the socials 
5. sends data to local db & nk uncle's webhook

'''

# import modules
import open_entry_chart
from traceback import print_exc
from resources.symbol_settings import symbol_category
import send_to_socials.send_to_discord as send_to_discord
import database.nk_db as nk_db
import database.local_db as local_db
from time import sleep, time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from json import loads



# class
class Alerts:

  def __init__(self, drawer_indicator, screener_shortitle, driver, hour_tracker_name, chart_timeframe, timeout) -> None:
    self.driver = driver
    self.local_db = local_db.Database()
    self.nk_db = nk_db.Post()
    self.chart = open_entry_chart.OpenChart(self.driver)
    self.discord = send_to_discord.Discord()
    self.drawer_indicator = drawer_indicator
    self.screener_shortitle = screener_shortitle
    self.hour_tracker_name = hour_tracker_name
    self.chart_timeframe = chart_timeframe
    self.timeout = timeout
    
  def post(self, msg, screener_visibility):
    '''This goes through every entry in `msg` and takes a snapshot of it and posts it to Nk uncle's database and Poolsifi.'''
    try:
      screener_visibility(False, self.screener_shortitle) # hide the screener indicator with the passed in function
      
      for key, value in msg.items(): # go over every json field in this specific alert message
        timeframe = value['timeframe']
        entry_time = value['entryTime']
        entry_price = value['entryPrice']
        sl_price = value['slPrice']
        tp1_price = value['tp1Price']
        direction = value['direction']
        self.chart.change_symbol(key)
        self.chart.change_tframe(timeframe)
        self.chart.change_indicator_settings(self.drawer_indicator, entry_time, entry_price, sl_price, tp1_price, value['tp2Price'], value['tp3Price'])

        chart_link = self.chart.save_chart_img() 
        category = symbol_category(key)
        content = f"{direction} in {key} at {entry_price}. Takeprofit: {tp1_price} Stoploss: {sl_price} {chart_link}"
        self.discord.create_msg(category, content) 
        self.send_to_db(value['type'], direction, key, timeframe, entry_price, tp1_price, sl_price, chart_link, content, entry_time, category, '')
        
      self.chart.change_tframe(self.chart_timeframe) # change back to the original timeframe which was set in open_tv.py
    except Exception as e:
      print_exc()

  def send_to_db(self, _type, direction, symbol, tframe, entry_price, tp, sl, chart_link, content, date_time, symbol_type, exit_msg):
    data = {
      "type": _type,
      "direction": direction,
      "symbol": symbol,
      "tframe": tframe,
      "entry": entry_price,
      "tp": tp,
      "sl": sl,
      "chart_link": chart_link,
      "content": content,
      "date": date_time,
      "symbol_type": symbol_type,
      "exit_msg": exit_msg
    }

    self.local_db.add_doc(data)
    self.nk_db.post_to_url(data)

  def read_and_parse(self):
    '''Reads the alert from the Alert log and turns the alert's message into JSON and is returned'''
    start_time = time()
    count = 0 # the toal no. of times an error has come
    alert_box = None
    while True:
      try:
        alert_box = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="message-PQUvhamm"]')))
        break
      except Exception as e:
        print_exc()
        if count == 0: # fix an error (if there is one) and wait for 1 minute. 
          if self.fix_error():
            start_time = time()
            count += 1

        if time() - start_time >= self.timeout:
          print("Timeout reached. Can't wait any longer for alert message.")
          break
        continue

    return loads(alert_box.text) if alert_box != None else loads('{}')# the alert message is jsonified

  def read_hour_tracker_alert(self):
    '''checks if an alert from the Hour tracker indicator has come in the Alerts log. If it has it removes it from the alert log and returns it as a web element '''
    val = None
    loop_brk = False
    while True:
      try:
        alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
        alert_names = [el.find_element(By.CSS_SELECTOR, 'div[class="name-PQUvhamm"]').text for el in alert_boxes]
        for i, name in enumerate(alert_names):
          if self.hour_tracker_name in name:
            val = alert_boxes[i]
            self.delete_hour_tracker_notif(val)
            loop_brk = True
            break
        if loop_brk:
          break
      except Exception as e:
        print_exc()
        continue

    return val
  
  def delete_hour_tracker_notif(self, alert):
    '''this removes the alert (which came from the hour tracker indicator) from the alerts log'''
    if alert != None:
      ActionChains(self.driver).move_to_element(alert).perform()
      alert.find_element(By.CSS_SELECTOR, 'div[title="Remove"]').click()
      sleep(1) # wait for the alert to be removed from the alerts log
      
  def fix_error(self):
    '''checks if the alert has a Stopped - Calculation error. If it has an error, it clicks the restart button.
    Returns `True` if there's an error'''
    val = False
    alert = self.driver.find_element(By.CSS_SELECTOR, '.list-G90Hl2iS div.itemBody-ucBqatk5')
    if alert.find_element(By.CSS_SELECTOR, 'span[data-name="alert-item-status"]').text == 'Stopped — Calculation error':
      # click on restart
      val = True
      ActionChains(self.driver).move_to_element(alert).perform()
      alert.find_element(By.CSS_SELECTOR, 'div[data-name="alert-restart-button"]').click()
    
    return val
