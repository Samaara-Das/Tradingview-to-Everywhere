'''This module is for checking for exits'''

import pytz
import logger_setup
from datetime import datetime, timedelta, time
from time import sleep

# Set up logger for this file
exit_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

INDICATOR_SHORT = 'Get Exits' # shorttitle of the Get Exits indicator
INDICATOR_NAME = 'Get Exits' # name of the Get Exits indicator
GET_EXITS_LAYOUT_NAME = 'Exits' # Name of the layout on TradingView
DAYS = 2 # all the entries within this timespan will be retrieved
DAYS_TO_RUN = [0, 1, 2, 3, 4, 5, 6] # the days of the week on which this application should check for entries in each of the collections. 0 is for Monday and 6 is for Sunday

class Exits:
    def __init__(self, database, open_entry_chart, browser) -> None:
        self.open_chart = open_entry_chart
        self.browser = browser
        self.database = database
        self.collections = ['US Stocks', 'Currencies', 'Crypto', 'Indian Stocks'] # names of the mongodb collections
        self.local_tz = pytz.timezone('Asia/Kolkata')
        self.yesterday = datetime.now(self.local_tz) - timedelta(days=1)
        self.checked_categories = {category:self.yesterday.date() for category in self.collections}
        self.browser.change_layout(GET_EXITS_LAYOUT_NAME)

    def check_exits(self):
        try:
            # Check market timings for each collection
            for col in self.collections:
                self.remove_duplicate_entries(col) # Remove all the duplicate entries in each collection so that the same entries don't get posted twice in the Discord channel

                # If this category has already been gone through for today, skip to the next category
                # This makes sure that each category's entries are only checked once a day
                now = datetime.now(self.local_tz).date()
                if self.checked_categories[col] == now:
                    continue

                # Check if certain categories can run when their market is open so that new ticks can come in their market. If new ticks come, alerts for the Get Exits indicator will be able to run. 
                # Also, make sure that this can run on certain days in a week like Tue and Thur. There's no need to run it everyday and running it once a week might be too late to check for the exits of entries.
                est_tz = pytz.timezone('America/New_York') 
                now_in_est = datetime.now(est_tz)

                if col == 'Indian Stocks':
                    now_in_ist = datetime.today() # Indian Standard Time
                    if not (self.indian_market_timing_valid() == True and now_in_ist.weekday() in DAYS_TO_RUN):
                        continue

                if col == 'US Stocks':
                    if not (self.us_market_timing_valid() == True and now_in_est.weekday() in DAYS_TO_RUN):
                        continue

                if col == 'Currencies':
                    if not (self.forex_market_timing_valid() == True and now_in_est.weekday() in DAYS_TO_RUN):
                        continue

                if col == 'Crypto':
                    if not (now_in_est.weekday() in DAYS_TO_RUN):
                        continue

                # Retrieve entries
                entries = self.database.get_entries_in_timespan(col, self.database.get_unix_time(DAYS))

                # get the entries that are still running and haven't hit tp3 yet but have maybe hit tp1 or tp2.
                # By getting the entries that have just hit their tp1 or tp2 levels, we will be able to check whether those entries have hit higher tp levels. Eg: If a trade that hit tp1 can go to tp2 or if a trade that hit tp2 can go to tp3
                entries = [entry for entry in entries if not entry['sl_hit'] and not entry['tp3_hit']]

                # Send each retrieved entry’s info into the indicator’s inputs
                wins = 0 # total number of entries in this collection that hit any of their TP levels
                losses = 0 # total number of entries in this collection that hit any their SL levels
                for entry in entries:
                    # open the symbol and the timeframe
                    if self.open_chart.change_symbol(entry['symbol']) and self.open_chart.change_tframe(entry['tframe']):
                        sleep(1)

                        # open and change the indicator's settings
                        if self.open_chart.change_get_exit_settings(INDICATOR_SHORT, int(entry['date']), float(entry['entry']), entry['direction'], float(entry['sl']), float(entry['tp1']), float(entry['tp2']), float(entry['tp3'])):
                        
                            # set an alert
                            self.browser.get_exits_shorttitle = INDICATOR_SHORT
                            self.browser.get_exits_indicator = self.browser.get_indicator(self.browser.get_exits_shorttitle)
                            if self.browser.set_get_exit_alert(self.browser.get_exits_shorttitle, int(entry['date']), float(entry['entry']), entry['direction'], float(entry['sl']), float(entry['tp1']), float(entry['tp2']), float(entry['tp3'])):

                                # wait for an alert to come
                                alerts = self.browser.alerts
                                stats = alerts.get_exit_alert(self.browser.get_exits_shorttitle, entry['symbol'])

                                if stats:
                                    # update the entry with the stats
                                    tp1_hit = True if stats['tp1_hit'] == 'true' else False
                                    tp2_hit = True if stats['tp2_hit'] == 'true' else False
                                    tp3_hit = True if stats['tp3_hit'] == 'true' else False
                                    sl_hit = True if stats['sl_hit'] == 'true' else False

                                    self.database.db[col].update_one({'_id': entry['_id']}, {'$set': {'tp1_hit': tp1_hit, 'tp2_hit': tp2_hit, 'tp3_hit': tp3_hit, 'sl_hit': sl_hit}})

                                    # update the number of wins and losses
                                    if sl_hit: 
                                        losses = losses + 1 

                                    if tp1_hit or tp2_hit or tp3_hit: 
                                        wins = wins + 1 
 
                                    # take a snapshot
                                    if tp1_hit or tp2_hit or tp3_hit or sl_hit:
                                        exit_logger.info(f'An exit has been hit. Going to take a snapshot. Exits: sl-{sl_hit}, tp1-{tp1_hit}, tp2-{tp2_hit}, tp3-{tp3_hit}')
                                        snapshot_link = alert.post()
                                        if snapshot_link:
                                            # add the link to the document
                                            self.database.db[col].update_one({'_id': entry['_id']}, {'$set': {'exit_snapshot': snapshot_link}})

                                            # send the message to Discord
                                            discord = send_to_discord.Discord()
                                            symbol = entry['symbol']
                                            category = symbol_settings.symbol_category(symbol)
                                            word = 'hit' if sl_hit else ('gained' if tp1_hit or tp2_hit or tp3_hit else 'none')
                                            exit_type = 'Stop Loss' if sl_hit else ('3%' if tp3_hit else '2%' if tp2_hit else '1%' if tp1_hit else 'none')
                                            content = f"{entry['direction']} trade in {symbol} {word} {exit_type}. Link: {snapshot_link}"
                                            discord.create_msg(category, content) 

                                # delete the alert
                                browser.delete_all_alerts()

                    checked_categories[col] = now.date() # update the date that this category was checked
        
        except Exception as e:
            exit_logger.exception('Error encountered: ')

    def remove_duplicate_entries(self, col):
        '''This removes the duplicate document in `col` so that each document can be unique. Entries are considered duplicates if their direction, symbol and date fields match another document.'''
        collection = self.database.db[col]
        pipeline = [ # Stage 1: Match and group documents by 'direction', 'symbol', and 'date', while collecting their _ids
            {
                '$group': {
                    '_id': {'direction': '$direction','symbol': '$symbol','date': '$date'},
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
 