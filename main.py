'''
this is the main module which starts everything.
'''

import logger_setup
import open_tv
import exits as get_exits
import time as time_module

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
            exits = get_exits.Exits(browser.alerts.local_db, browser.open_chart, browser)
            while True:
                # restart all the inactive alerts every INTERVAL_MINUTES minutes (this is also done in get_alert_data.py in the method get_alert_box_and_msg()) and refresh browser
                if time_module.time() - last_run > interval_seconds:
                    browser.alerts.restart_inactive_alerts()
                    last_run = time_module.time()

                # instantiate the Exits class 
                exits.delete_all_get_exits_alerts()

                # do the setup again so that posting of the entries can happen
                if browser.re_setup():
                    # get entries from the alerts which come and post them
                    browser.alerts.post_entries(browser.indicator_visibility)

                # check for exits
                if exits.set_up():
                    exits.check_exits()

    except Exception as e:
        main_logger.exception(f'Error in main.py:')
 