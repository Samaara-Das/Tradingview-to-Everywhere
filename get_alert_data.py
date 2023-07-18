'''
This module gets the entry signals from the premium screener on tradingview 
by getting text from alerts
'''

# import modules
import time
import open_entry_chart
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# class
class Alerts:

  def __init__(self, driver) -> None:
    self.driver = driver

    # open a new tab
    self.chart = open_entry_chart.OpenChart(self.driver)
    self.chart.open_new_tab()
    self.chart.switch_to_old_tab()
    
  def read_alert(self, msg):
    buy_list = []
    sell_list = []
    closed_buy_list = []
    closed_sell_list = []

    lines = msg.split('\n')
    self.close_alert()

    for line in lines:
      parts = line.split('|')
      if 'Buy' in line or 'Sell' in line:
        self.change_symbol_tframe(parts[4], parts[5])

  def close_alert(self):
    ok_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".button-D4RPB3ZC.size-small-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC")))
    ok_button.click()

  def change_symbol_tframe(self, symbol, timeframe):
    self.chart.switch_to_new_tab()
    self.chart.change_symbol(symbol)
    self.chart.change_tframe(timeframe)
    self.chart.switch_to_old_tab()

  def get_data_from_alert(self):

    while True:
      try:
        alert_msg = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.secondaryRow-QkiHQU0S")))
        self.read_alert(alert_msg.text)
        alert_msg = None
      except Exception as e:
        continue
      


