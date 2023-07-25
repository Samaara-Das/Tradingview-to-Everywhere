'''
This module gets the entry signals from the premium screener on tradingview 
by getting text from alerts
'''

# import modules
import time
import sqlite3
import open_entry_chart
import send_tweet
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# database setup
DB_NAME = 'alerts.db' 
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()
trade_counter = 0 #to track and access the trades

# class
class Alerts:

  def __init__(self, driver) -> None:
    self.driver = driver
    create_database()
    self.chart = open_entry_chart.OpenChart(self.driver)
    self.tweet = send_tweet.TwitterClient()
    
  def read_alert(self, msg):
    lines = msg.split('\n')
    self.close_alert()

    for line in lines:
      parts = line.split('|')
      print(line)
      if 'Closed' not in line: #if this line is about an entry not an exit
        symbol = parts[4]
        entry_price = parts[1]
        _type = parts[0]
        self.chart.change_symbol(symbol)
        self.chart.change_tframe(parts[5])
        self.chart.change_indicator_settings('Entry', _type, entry_price, parts[2], parts[3])
        self.tweet.create_tweet(_type + ' in ' + symbol + ' at ' + entry_price + '.' + self.chart.save_chart_img())

      elif 'TP' in line or 'SL' in line: #if this line is about a close which hit tp
        symbol = parts[5]
        entry_price = parts[2]
        _type = parts[0]
        self.chart.change_symbol(symbol)
        self.chart.change_tframe(parts[6])
        self.chart.change_indicator_settings('Exit', _type, entry_price, parts[3], parts[4], parts[7])
        self.tweet.create_tweet(_type + ' Closed in ' + symbol + ' at TP!!' + self.chart.save_chart_img())


  def close_alert(self):
    ok_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".button-D4RPB3ZC.size-small-D4RPB3ZC.color-brand-D4RPB3ZC.variant-primary-D4RPB3ZC")))
    ok_button.click()

  def send_to_twitter(self):
    while True:
      try:
        alert_msg = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.secondaryRow-QkiHQU0S")))
        self.read_alert(alert_msg.text)
        alert_msg = None
      except Exception as e:
        continue
      


def create_database():
  with conn:
    cur.execute('''CREATE TABLE IF NOT EXISTS alerts 
                (trade_counter INTEGER PRIMARY KEY,
                type text, 
                symbol TEXT, 
                tframe INTEGER, 
                entry REAL, 
                tp REAL, 
                sl REAL,
                chart_link TEXT, 
                date TEXT)''')

def fill_database(_type, symbol, tframe, entry, tp, sl, chart_link, date):
  with conn:
    trade_counter += 1
    cur.execute('''INSERT INTO alerts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)''', (trade_counter, _type, symbol, tframe, entry, tp, sl, chart_link, date))

def get_last_row():
  with conn:
    # Execute the query and fetch the last row
    cur.execute("SELECT * FROM alerts")
    last_rows = cur.fetchall()
    print('\nlatest rows: ', last_rows[-1])

  return last_rows[-1]

