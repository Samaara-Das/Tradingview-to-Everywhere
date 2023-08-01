'''
This module gets the entry signals from the premium screener on tradingview 
by getting text from alerts
'''

# import modules
import open_entry_chart
import send_tweet
import send_to_discord
from time import sleep
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# database setup
trade_counter = 0 #to track and access the trades

# class
class Alerts:

  def __init__(self, driver, browser) -> None:
    self.driver = driver
    self.chart = open_entry_chart.OpenChart(self.driver)
    self.tweet = send_tweet.TwitterClient()
    self.discord = send_to_discord.Discord()
    self.browser = browser
    
  def read_alert(self, msg):
    lines = msg.split('\n')

    for line in lines:
      parts = line.split('|')
      symbol = None
      entry_price = None
      direction = None
      tframe = None
      tp = None
      sl = None
      time_of_entry = None
      content = ' '
      _type = 'Entry' if 'TP' not in line and 'SL' not in line else 'Exit'

      if _type == 'Exit':
        symbol, entry_price, direction, tframe, tp, sl, time_of_entry = (parts[5], parts[2], parts[0], parts[6], parts[3], parts[4], parts[7])
        content = f"{direction} closed in {symbol} at TP!! {{}}"
      else:
        symbol, entry_price, direction, tframe, tp, sl = (parts[4], parts[1], parts[0], parts[5], parts[2], parts[3])
        content = f"{direction} in {symbol} at {entry_price} {{}}"

      self.chart.change_symbol(symbol)
      self.chart.change_tframe(tframe)
      self.chart.change_indicator_settings(_type, direction, entry_price, tp, sl)
      chart_link = self.chart.save_chart_img()
        
      if not symbol.isdigit() and self.browser.is_signal_indicator_loaded():
        self.tweet.create_tweet(content.format(chart_link))
        self.discord.create_msg(content.format(chart_link))
      else:
        print('signal indicator did not successfully load OR the symbol was a number')

  def close_alert(self):
    ok_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".button-D4RPB3ZC.size-small-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC")))
    ok_button.click()

  def send_to_twitter(self):
    message = ''
    while True:
      try:
        alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="message-PQUvhamm"]')))
        alert_boxes = alert_boxes[::-1] #to make the oldest alerts come first in the list to post about the oldest alerts first

        for alert_box in alert_boxes:
          text = '\n'.join(alert_box.text.split(' '))
          message += text

        if len(alert_boxes) > 0:
          self.clear_log()    

        self.read_alert(message) 
        message = '' 
        alert_box = None
      except Exception as e:
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
