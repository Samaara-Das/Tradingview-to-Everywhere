'''This module is for checking for exits'''

import pytz
import logger_setup
from datetime import datetime, timedelta, time
from time import sleep
from resources.symbol_settings import symbol_category
from send_to_socials.discord import Discord
from send_to_socials.twitter import TwitterClient
from send_to_socials._facebook import post_before_after as fb_post
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException

# Set up logger for this file
exit_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

BI_REPORT_LINK = 'https://bit.ly/trade-stats' # link to the bi report
INDICATOR_SHORT = 'Get Exits' # shorttitle of the Get Exits indicator
INDICATOR_NAME = 'Get Exits' # name of the Get Exits indicator
GET_EXITS_LAYOUT_NAME = 'Exits' # Name of the layout on TradingView
DAYS = 15 # all the entries within this timespan will be retrieved
DAYS_TO_RUN = [0, 1, 2, 3, 4, 5, 6] # the days of the week on which this application should check for entries in each of the collections. 0 is for Monday and 6 is for Sunday

class Exits:
    def __init__(self, database, open_entry_chart, browser) -> None:
        self.open_chart = open_entry_chart
        self.browser = browser
        self.database = database
        self.col = 'Entries'
        self.last_checked_dates = {
            'Currencies': None,
            'US Stocks': None,
            'Indian Stocks': None,
            'Crypto': None
        }
        self.local_tz = pytz.timezone('Asia/Kolkata')
        self.browser.get_exits_shorttitle = INDICATOR_SHORT
        self.browser.get_exits_name = INDICATOR_NAME
        self.alert_name = self.browser.get_exits_shorttitle
        self.discord = Discord()
        self.twitter = TwitterClient()

    def set_up(self):
        '''Sets up Tradingview for checking the exits'''
        try:
            if not self.browser.save_layout(): # save the current layout so that it a popup won't come and interfere with the application
                return
            
            if not self.browser.change_layout(GET_EXITS_LAYOUT_NAME):
                return
            sleep(3)

            if not self.browser.change_candles_type('Line'):
                return

            self.browser.get_exits_indicator = self.browser.get_indicator(self.browser.get_exits_shorttitle)
            return True
        except Exception as e:
            exit_logger.exception(f'Error in set_up(): {e}')
            return False

    def delete_all_get_exits_alerts(self):
        '''Deletes all the alerts that have an alert name that is `self.alert_name`. Note: the alerts that get checked are just the ones that are first visible without scrolling down.'''
        try:
            sleep(1)
            # wait for the alert sidebar to show up
            alert_sidebar = WebDriverWait(self.browser.driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.body-i8Od6xAB')))
            if not alert_sidebar:
                exit_logger.error('Alert sidebar not found. Cannot delete all alerts.')
                return False

            alerts = alert_sidebar[0].find_elements(By.CSS_SELECTOR, 'div[class="itemBody-ucBqatk5 active-Bj96_lIl"]')

            for i, alert in enumerate(alerts):
                if i > 0: # If there are many alerts, wait for some time before deleting the next alert so that the ElementNotInteractableException won't occur
                    sleep(0.5)

                # If the alert's name is "Get Exits"
                if alert.find_element(By.CSS_SELECTOR, 'div[data-name="alert-item-name"]').text == self.alert_name:
                    # Delete it
                    ActionChains(self.browser.driver).move_to_element(alert).perform()
                    remove_button = alert.find_element(By.CSS_SELECTOR, 'div[data-name="alert-delete-button"]')
                    remove_button.click()
                    # Wait for the confirmation popup to appear and click "Yes"
                    popup = WebDriverWait(self.browser.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]')))
                    popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
                    exit_logger.info(f'Deleted alert with name {self.alert_name}')
    
            return True
        except Exception as e:
            exit_logger.exception(f'An error occurred while deleting all the Get Exits alerts. Error:')
            return False

    def get_exit_alert(self, entry):
        '''This opens the chart with the symbol of the entry, opens the Get Exit indicator, changes its settings, sets an alert for it and wait for its message to come in Alert Logs. Then, it returns the message. If there's an error, `False` will be returned.'''
        try:
            # open the symbol and the timeframe
            entry_symbol = entry['symbol']
            if self.open_chart.change_symbol(entry_symbol) and self.open_chart.change_tframe(entry['timeframe']):
                sleep(1)
                indicator_inputs = [int(entry['unixTime']), entry['entryPrice'], entry['direction'], entry['slPrice'], entry['tp1Price'], entry['tp2Price'], entry['tp3Price']]
                # open and change the indicator's settings
                if self.open_chart.change_get_exit_settings(INDICATOR_SHORT, *indicator_inputs):
                    # set an alert
                    if self.browser.set_get_exit_alert(self.alert_name, *indicator_inputs):
                        # wait for an alert to come
                        alerts = self.browser.alerts
                        alert_message = alerts.get_exit_alert(self.alert_name, entry_symbol)
                        return alert_message
        except Exception as e:
            exit_logger.exception(f'An error occurred in the get_exit_alert method. Error:')
            return False

    def check_exits(self):
        '''This checks if entries in the `self.col` collection have been exited. If they have, the entries get updated with its exit and the exit gets posted on Discord.'''
        try:
            if not self.delete_all_get_exits_alerts(): # Delete Get Exits alerts if there are any to prevent new alerts from coming
                exit_logger.error(f'Failed to delete the alerts named Get Exits. Trying again.')

            categories = self.last_checked_dates.keys()
            today = datetime.now(self.local_tz).date() # today's date

            # Remove all the duplicate entries so that the same entries don't get posted twice in the Discord channel
            self.remove_duplicate_entries(self.col) 

            for category in categories:
                # Check if certain categories can run when their market is open so that new ticks can come in their market. If new ticks come, alerts for the Get Exits indicator will be able to run. 
                # Also, make sure that this can run on certain days in a week like Tue and Thur. There's no need to run it everyday and running it once a week might be too late to check for the exits of entries.
                if self.is_market_open(category):
                    # If this category has already been gone through for today, skip to the next category
                    # This makes sure that each category's entries are only checked once a day
                    if (self.last_checked_dates[category] is None or self.last_checked_dates[category] != today):
                        # Retrieve entries
                        entries = self.database.get_entries_in_timespan(self.col, category, self.database.get_unix_time(DAYS))

                        # get the entries that are still running and haven't hit tp3 yet but have maybe hit tp1 or tp2.
                        # By getting the entries that have just hit their tp1 or tp2 levels, we will be able to check whether those entries have hit higher tp levels. Eg: If a trade that hit tp1 can go to tp2 or if a trade that hit tp2 can go to tp3
                        entries = [entry for entry in entries if not entry['isSlHit'] and not entry['isTp3Hit']]

                        # Check if each entry exited
                        for entry in entries:
                            # Set up an alert for this entry and get the alert
                            stats = self.get_exit_alert(entry)

                            if stats:
                                # update the entry with the stats
                                tp1_hit = True if stats['isTp1Hit'] == 'true' else False
                                tp2_hit = True if stats['isTp2Hit'] == 'true' else False
                                tp3_hit = True if stats['isTp3Hit'] == 'true' else False
                                sl_hit = True if stats['isSlHit'] == 'true' else False

                                self.database.db[self.col].update_one({'_id': entry['_id']}, {'$set': {'isTp1Hit': tp1_hit, 'isTp2Hit': tp2_hit, 'isTp3Hit': tp3_hit, 'isSlHit': sl_hit}})

                                # take a snapshot
                                if tp1_hit or tp2_hit or tp3_hit or sl_hit:
                                    exit_logger.info(f'An exit has been hit. Going to take a snapshot. Exits: sl-{sl_hit}, tp1-{tp1_hit}, tp2-{tp2_hit}, tp3-{tp3_hit}')
                                    links = self.open_chart.get_exit_snapshot(self.browser.get_exits_shorttitle)
                                    if links:
                                        png_link, tv_link = links['png'], links['tv'] 
                                        # add the link to the document
                                        self.database.db[self.col].update_one({'_id': entry['_id']}, {'$set': {'tvExitSnapshot': tv_link, 'pngExitSnapshot': png_link}})

                                        # send the message to the exits channel
                                        symbol = entry['symbol']
                                        category = symbol_category(symbol)
                                        word = 'hit' if sl_hit else ('gained' if tp1_hit or tp2_hit or tp3_hit else 'none')
                                        exit_type = 'Stop Loss' if sl_hit else ('3%' if tp3_hit else '2%' if tp2_hit else '1%' if tp1_hit else 'none')
                                        exit_content = f"{entry['direction']} trade in {symbol} {word} {exit_type}. Link: {png_link}"
                                        bi_content = f'For more stats, go here: {BI_REPORT_LINK}'
                                        
                                        self.discord.send_to_exit_channel(category, exit_content) 

                                        self.discord.send_to_before_and_after_channel(entry['category'], entry['pngEntrySnapshot'], entry['pngExitSnapshot'], bi_content) 

                                        self.twitter.before_after_tweets(entry['tvEntrySnapshot'], entry['tvExitSnapshot'], entry['content'], exit_content)
                                        
                                        fb_post(entry['pngEntrySnapshot'], entry['pngExitSnapshot'], entry['content']+'\n'+bi_content, exit_content+'\n'+bi_content) 

                            # delete the alert made by Get Exits
                            if not self.delete_all_get_exits_alerts():
                                exit_logger.error(f'Failed to delete the alerts named Get Exits. Trying again.')
                                self.delete_all_get_exits_alerts()

                        # Update the last checked date for this category
                        self.last_checked_dates[category] = today

        except Exception as e:
            exit_logger.exception('Error encountered: ')
            # delete the alert made by Get Exits
            if not self.delete_all_get_exits_alerts():
                exit_logger.error(f'Failed to delete the alerts named Get Exits. Trying again.')
                self.delete_all_get_exits_alerts()

    def market_not_on_holiday(self):
        '''This returns `True` if the market is open and not on a holiday/currently in the pre-post market time'''
        if self.browser.driver.find_elements(self.browser.By.CSS_SELECTOR, 'div[class="statusItem-Lgtz1OtS small-Lgtz1OtS marketStatusOpen-Lgtz1OtS"]'):
            return True
        else:
            return False

    def remove_duplicate_entries(self, col):
        '''This removes the duplicate document in `col` collection so that each document can be unique. Entries are considered duplicates if their direction, symbol, category and unixTime fields match another document.'''
        try:
            collection = self.database.db[col]
            pipeline = [
                {
                    '$group': {
                        '_id': {'direction': '$direction', 'symbol': '$symbol', 'category': '$category', 'unixTime': '$unixTime'},
                        'docs': {'$push': '$_id'},
                        'count': {'$sum': 1}
                    }
                },
                {
                    '$match': {'count': {'$gt': 1}}
                }
            ]

            duplicate_groups = list(collection.aggregate(pipeline))
            ids_to_delete = []
            for group in duplicate_groups:
                ids_to_delete.extend(group['docs'][1:]) # Skip the first id to keep one document from each group

            if ids_to_delete: # Delete the documents with the collected _id values
                delete_result = collection.delete_many({'_id': {'$in': ids_to_delete}})
                exit_logger.info(f"Deleted {delete_result.deleted_count} duplicates from the {col} collection.")
            else:
                exit_logger.info(f"No duplicates to delete in {col} collection.")     
        except Exception as e:
            exit_logger.exception('Error encountered: ')
            return False

    def is_market_open(self, col):
        '''This checks if the `col` market ic currently open. Returns `True` if it is and `False` if it isn't.'''
        est_tz = pytz.timezone('America/New_York') 
        now_in_est = datetime.now(est_tz)

        if col == 'Indian Stocks':
            now_in_ist = datetime.today() # Indian Standard Time
            if not (self.indian_market_timing_valid() == True and now_in_ist.weekday() in DAYS_TO_RUN):
                return False

        if col == 'US Stocks':
            if not (self.us_market_timing_valid() == True and now_in_est.weekday() in DAYS_TO_RUN):
                return False

        if col == 'Currencies':
            if not (self.forex_market_timing_valid() == True and now_in_est.weekday() in DAYS_TO_RUN):
                return False

        if col == 'Crypto':
            if not (now_in_est.weekday() in DAYS_TO_RUN):
                return False
        
        return True

    def indian_market_timing_valid(self):
        '''This returns `True` if the Indian markets are open i.e. the current time should be within 9:30 AM - 3:35 PM Monday to Friday IST. `False` otherwise.'''
        now = datetime.now() # Get the current local date and time
        is_weekday = now.weekday() in range(0, 5)  # Check if the current day is between Monday and Friday (Monday is 0, Sunday is 6)

        # Time range: 9:30 AM to 3:35 PM
        start_time = time(9, 30)
        end_time = time(15, 35)

        is_within_time_range = start_time <= now.time() <= end_time # Check if the current time is within the range
        return is_weekday and is_within_time_range

    def us_market_timing_valid(self):
        '''This returns `True` if the US markets are open i.e. the current time should be within 9:30 AM to 4:00 PM from Monday to Friday EST. `False` otherwise.'''
        new_york_tz = pytz.timezone('America/New_York') # Define New York timezone
        now_in_new_york = datetime.now(new_york_tz) # Get the current time in New York
        
        # Check if today is a weekday (Monday is 0, Sunday is 6)
        if now_in_new_york.weekday() not in range(0, 5):  # If it's not Monday to Friday
            return False
        
        # Define start and end times
        start_time = time(hour=9, minute=30)
        end_time = time(hour=16, minute=0)  # 4 PM
        
        # Check if current time is within working hours
        return start_time <= now_in_new_york.time() <= end_time
    
    def forex_market_timing_valid(self):
        '''This returns `True` if the Forex markets are open i.e. the current time should be within Sunday 5:00 PM EST to Friday 5:00 PM EST. `False` otherwise.'''
        est_tz = pytz.timezone('America/New_York') # Define EST timezone
        now_in_est = datetime.now(est_tz) # Get the current time in EST

        # Check if today is within Sunday 5:00 PM to the end of Friday
        if now_in_est.weekday() == 6:
            start_time = time(hour=17)
            if now_in_est.time() < start_time: # Check if current time is past 5:00 PM on Sunday
                return False
        elif now_in_est.weekday() == 5: # Always false if it's Saturday
            return False 
        elif now_in_est.weekday() == 4: # Friday
            end_time = time(hour=17) 
            if now_in_est.time() > end_time: # Check if current time is past 5:00 PM on Friday
                return False
                
        return True # If it's not Saturday, before 5:00 PM on Sunday, or after 5:00 PM on Friday, return True
 