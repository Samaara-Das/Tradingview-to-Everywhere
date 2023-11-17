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
from resources.symbol_settings import symbol_category
import send_to_socials.send_to_discord as send_to_discord
import database.nk_db as nk_db
import database.local_db as local_db
from time import sleep, time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from json import loads



# class
class Alerts:

  def __init__(self, drawer_indicator, driver) -> None:
    self.driver = driver
    self.local_db = local_db.Database()
    self.nk_db = nk_db.Post()
    self.chart = open_entry_chart.OpenChart(self.driver)
    self.discord = send_to_discord.Discord()
    self.drawer_indicator = drawer_indicator
    
  def post(self, msg):
    '''This goes through every entry in `msg` and takes a snapshot of it and posts it to Nk uncle's database and Poolsifi.'''
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
    timeout = 60 # 60 seconds
    alert_box = None
    while True:
      try:
        alert_box = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="message-PQUvhamm"]')))
        break
      except Exception as e:
        elapsed_time = time() - start_time
        if elapsed_time >= timeout:
          print("Timeout reached. Exiting the loop.")
          break
        continue

    return loads(alert_box.text) if alert_box != None else loads('{}')# the alert message is jsonified

