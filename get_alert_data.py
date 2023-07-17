'''
This module gets the entry signals from the premium screener on tradingview 
by getting text from alerts
'''

# import modules
import open_entry_chart
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# class
class Alerts:

  def __init__(self, driver) -> None:
    self.driver = driver

    # open a new tab
    self.chart = open_entry_chart.OpenChart(self.driver, 0, 0, 0, '', '')
    self.chart.open_new_tab()

  def read_alert(self, msg):
    buy_list = []
    sell_list = []
    closed_buy_list = []
    closed_sell_list = []

    lines = msg.split('\n')
    self.close_alert()

    for line in lines:
      parts = line.split('|')

      if 'Buy' in line:
        buy_list.append({'entry': parts[1], 'tp': parts[2], 'sl': parts[3], 'symbol': parts[4], 'timeframe': parts[5]})
        print(buy_list[len(buy_list)-1])

      if 'Sell' in line:
        sell_list.append({'entry': parts[1], 'tp': parts[2], 'sl': parts[3], 'symbol': parts[4], 'timeframe': parts[5]})
        print(sell_list[len(sell_list)-1])

      # if 'Closed Sell' in line and 'TP' in line: 
      #   closed_sell_list.append({'entry': parts[0], 'symbol': parts[1], 'timeframe': parts[2]})
      #   print(closed_sell_list[len(closed_sell_list)-1])

      # if 'Closed Buy' in line and 'TP' in line:
      #   closed_buy_list.append({'entry': parts[0], 'symbol': parts[1], 'timeframe': parts[2]})
      #   print(closed_buy_list[len(closed_buy_list)-1])

  def close_alert(self):
    ok_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".button-D4RPB3ZC.size-small-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC")))
    ok_button.click()

  def get_data_from_alert(self):

    while True:
      try:
        alert_msg = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.secondaryRow-QkiHQU0S")))
        self.read_alert(alert_msg.text)
        alert_msg = None
      except Exception as e:
        continue
      
