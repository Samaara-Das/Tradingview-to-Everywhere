'''
this is the main module which starts everything.
'''

import logger_setup
import open_tv
import exits as get_exits
import pytz
import time as time_module
from time import sleep
from datetime import datetime, time, timedelta

# Set up logger for this file
main_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

SCREENER_SHORT = 'Screener' # short title of the screener
DRAWER_SHORT = 'Trade' # short title of the trade drawer indicator 
SCREENER_NAME = 'Premium Screener' # name of the screener
DRAWER_NAME = 'Trade Drawer' # name of the trade drawer
REMOVE_LOG = True # remove the content of the log file (to clean it up)
INTERVAL_MINUTES = 5 # number of mins to wait until inactive alerts get reactivated and for the browser to refresh (refreshing will hopefully prevent the browser and this application from freezing)
START_FRESH = False
LINES_TO_KEEP = 400

# Convert the interval to seconds
interval_seconds = INTERVAL_MINUTES * 60

# Clean up the log
if REMOVE_LOG:
    with open('app_log.log', 'w') as file:
        pass

def trim_file(file_path, lines_to_keep):
    with open(file_path, 'r+', encoding='utf-8') as file:
        lines = file.readlines()
        # Keep only the last 'lines_to_keep' lines
        trimmed_lines = lines[-lines_to_keep:]
        file.seek(0)  # Go back to the start of the file
        file.writelines(trimmed_lines)  # Write the trimmed lines
        file.truncate()  # Remove the remaining lines

# Checking if the market is open for markets
def indian_market_timing_valid():
    '''This returns `True` if the Indian markets are open i.e. the current time should be within 9:30 AM - 3:35 PM Monday to Friday IST. `False` otherwise.'''
    now = datetime.now() # Get the current local date and time
    is_weekday = now.weekday() in range(0, 5)  # Check if the current day is between Monday and Friday (Monday is 0, Sunday is 6)

    # Time range: 9:30 AM to 3:35 PM
    start_time = time(9, 30)
    end_time = time(15, 35)

    is_within_time_range = start_time <= now.time() <= end_time # Check if the current time is within the range
    return is_weekday and is_within_time_range

def us_market_timing_valid():
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
    
def forex_market_timing_valid():
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

# to remove duplicate entries
def remove_duplicate_entries(db, col):
    '''This removes the duplicate document in `collection` so that each document can be unique. Entries are considered duplicates if their direction, symbol and date fields match another document.'''
    collection = db.db[col]
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
        main_logger.info(f"Deleted {delete_result.deleted_count} duplicates from the {col} collection.")
    else:
        main_logger.info(f"No duplicates to delete in {col} collection.")


# Run main code
if __name__ == '__main__':
    try:
        # Just a seperator to make the log look readable
        main_logger.info('***********************************************************************************')

        # initiate Browser
        browser = open_tv.Browser(True, SCREENER_SHORT, SCREENER_NAME, DRAWER_SHORT, DRAWER_NAME, INTERVAL_MINUTES, START_FRESH)

        # setup the indicators, alerts etc.
        setup_check = browser.setup_tv(trim_file, 'app_log.log', LINES_TO_KEEP)

        # set up alerts for all the symbols
        if START_FRESH:
            browser.set_bulk_alerts()

        if setup_check and browser.init_succeeded:
            last_run = time_module.time()
            while True:
                # restart all the inactive alerts every INTERVAL_MINUTES minutes (this is also done in get_alert_data.py in the method get_alert_box_and_msg()) and refresh browser
                if time_module.time() - last_run > interval_seconds:
                    browser.alerts.restart_inactive_alerts()
                    last_run = time_module.time()

                # get entries from the alerts which come and post them
                alert = browser.alerts.get_alert()
                browser.alerts.post(alert, browser.indicator_visibility)

                # check for exits
                exits = get_exits.Exits(browser.alerts.local_db, browser.open_chart, browser)
                exits.check_exits()

    except Exception as e:
        main_logger.exception(f'Error in main.py:')
 