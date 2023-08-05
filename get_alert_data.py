'''
This module gets the entry signals from the premium screener on tradingview 
by getting text from alerts
'''

# import modules
from traceback import format_exc
import open_entry_chart
import send_to_twitter
import send_to_discord
import nk_db
import local_db
from time import sleep
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# class
class Alerts:

  def __init__(self, driver, browser) -> None:
    self.driver = driver
    self.local_db = local_db.Database()
    self.nk_db = nk_db.Post()
    self.chart = open_entry_chart.OpenChart(self.driver)
    self.tweet = send_to_twitter.TwitterClient()
    self.discord = send_to_discord.Discord()
    self.browser = browser
    
  def read_alert(self, msg):
    lines = msg.split('\n')
    lines.pop(0) #remove the 0th index because it's just a blank line

    for line in lines:
      parts = line.split('|')
      symbol = None
      entry_price = None
      direction = None
      tframe = None
      tp = None
      sl = None
      date_time = None
      entry_time = None
      content = ' '
      exit_type = ' '
      _type = ' '
      if 'TP' not in line and 'SL' not in line:
        _type = 'Entry'
      elif 'TP' in line:
        _type = 'TP Exit'
        exit_type = 'TP!!'
      elif 'SL' in line: 
        _type = 'SL Exit'
        exit_type = 'SL'

      if _type == 'TP Exit':
        symbol, entry_price, direction, tframe, tp, sl, entry_time, date_time = (parts[5], parts[2], parts[0], parts[6], parts[3], parts[4], parts[7], parts[8])
        content = f"{direction} closed in {symbol} at {exit_type} {{}}"
      elif _type == 'Entry':
        symbol, entry_price, direction, tframe, tp, sl, entry_time = (parts[4], parts[1], parts[0], parts[5], parts[2], parts[3], parts[6])
        date_time = entry_time
        content = f"{direction} in {symbol} at {entry_price} {{}}"

      self.chart.change_symbol(symbol)
      self.chart.change_tframe(tframe)
      self.chart.change_indicator_settings(_type, direction, entry_price, tp, sl, entry_time)
      chart_link = self.chart.save_chart_img()

      content = content.format(chart_link)
      if _type == 'TP Exit' or _type == 'Entry':
        self.send_post_to_socials(symbol, content)
      self.send_to_db(_type, direction, symbol, tframe, entry_price, tp, sl, chart_link, content, date_time)


  def send_post_to_socials(self, symbol, content):
    is_symbol = not symbol.isdigit()
    is_ind_loaded = self.browser.is_signal_indicator_loaded()
    if is_symbol and is_ind_loaded:
      self.tweet.create_tweet(content)
      self.discord.create_msg(content)  
    else:
      print(f'from {__file__}: \nCould not send post. Signal indicator did not successfully load OR the symbol was a number.\nSymbol: ',symbol,' Indicator loaded: ',is_ind_loaded)

  def send_to_db(self, _type, direction, symbol, tframe, entry_price, tp, sl, chart_link, content, date_time):
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
      "date": date_time
    }

    self.local_db.add_doc(data)
    # self.nk_db.post_to_url(data)

  def read_and_parse(self):
    message = ''
    while True:
      try:
        alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="message-PQUvhamm"]')))
        alert_boxes = alert_boxes[::-1] #to make the oldest alerts come first in the list to post about the oldest alerts first

        for i, alert_box in enumerate(alert_boxes):
          _list = alert_box.text.split(' ')
          _list[0] = '\n' + _list[0]
          text = '\n'.join(_list)
          message += text

        if len(alert_boxes) > 0:
          self.clear_log()    

        self.read_alert(message) 
        message = '' 
        alert_box = None
      except Exception as e:
        print(f'error in {__file__}: \n{e} \nTraceback: {format_exc()}')
        continue
      
  def clear_log(self):
    # click the settings
    settings = self.driver.find_element(By.CSS_SELECTOR, 'div[data-name="alerts-log-actions-button"]')
    settings.click()

    # click on the "Clear log" dropdown option
    clear_log = self.driver.find_elements(By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')[-1]
    clear_log.click()

    # click OK when the confirm dialog pops up
    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="yes"]'))).click()

    # sleep to give it some time to delete the alert log
    sleep(1)



