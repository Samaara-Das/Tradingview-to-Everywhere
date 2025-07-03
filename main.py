"""
TradingView to Everywhere (TTE) - Main Entry Point

Purpose: This is the main entry point for the TradingView to Everywhere (TTE) application that automates trading signal distribution.

Functionality: This module initializes and manages the core application workflow:
1. Sets up the TradingView browser environment
2. Configures and creates alerts for trading symbols
3. Monitors the alert log for new trading signals
4. Processes and distributes trading signals to various platforms (Discord, Facebook, Twitter/X, MongoDB)
5. Periodically checks for trade exits and distributes exit information
6. Manages the application lifecycle including refreshing the browser and restarting inactive alerts

Dependencies:
- logger_setup.py: For application logging
- open_tv.py: For browser automation and TradingView interaction
- exits.py: For monitoring and processing trade exits
- GUI components (referenced but not directly imported here)

Usage: This file can be run directly to start the application in console mode,
or it can be imported and the run_trading_view function called with a status callback
to run the application with GUI status updates.
"""

import logger_setup
import open_tv
import exits as get_exits
import time as time_module

# Set up logger for this file
main_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

SCREENER_SHORT = 'Screener' # short title of the screener
DRAWER_SHORT = 'Trade Drawer 2' # short title of the trade drawer indicator 
SCREENER_NAME = 'Premium Screener' # name of the screener
DRAWER_NAME = 'Trade Drawer 2' # name of the trade drawer

# Additional screeners
SCREENER_OB_SHORT = "Order Block Screener"  # short title of the Order Block Screener
SCREENER_OB_NAME = "Order Block Screener"  # name of the Order Block Screener
SCREENER_NW_SHORT = "Nadaraya Watson Screener"  # short title of the Nadaraya Watson Screener
SCREENER_NW_NAME = "Nadaraya Watson Screener"  # name of the Nadaraya Watson Screener
SCREENER_SB_SHORT = "Structure break Screener"  # short title of the Structure break Screener
SCREENER_SB_NAME = "Structure break Screener"  # name of the Structure break Screener
REMOVE_LOG = True # remove the content of the log file (to clean it up)
INTERVAL_MINUTES = 10 # number of mins to wait until inactive alerts get reactivated and for the browser to refresh (refreshing will hopefully prevent the browser and this application from freezing)
START_FRESH = False

# Timeframe constants for screeners
SCREENER_TIMEFRAME_1 = "1 hour"  # First timeframe for screeners
SCREENER_TIMEFRAME_2 = "4 hours"  # Second timeframe for screeners  
SCREENER_TIMEFRAME_3 = "1 day"  # Third timeframe for screeners

# Timeframe ID mapping dictionary for TradingView dropdown
# Now using partial IDs (last 2 words) to handle dynamic ID changes
TIMEFRAME_ID_MAP = {
    "1 minute": "item_1",
    "5 minutes": "item_5",
    "10 minutes": "item_10",
    "15 minutes": "item_15",
    "30 minutes": "item_30",
    "1 hour": "item_60",
    "2 hours": "item_120",
    "3 hours": "item_180",
    "4 hours": "item_240",
    "8 hours": "item_480",
    "1 day": "item_1D",
    "1 week": "item_1W",
    "1 month": "item_1M",
    "3 months": "item_3M",
    "6 months": "item_6M"
}

# Convert the interval to seconds
interval_seconds = INTERVAL_MINUTES * 60

def run_trading_view(on_status_change=None):
    """
    Run the main TradingView monitoring loop.
    
    Args:
        on_status_change: Optional callback function to receive status updates.
                         Will be called with (status_message, is_error)
    
    Returns:
        None
    
    Raises:
        Exception: If initialization fails or any error occurs during execution
    """
    try:
        logger_setup.start_continuous_trim('app_log.log')

        # Just a separator to make the log look readable
        main_logger.info('Start ***********************************************************************************')

        if REMOVE_LOG:
            try:
                open('app_log.log', 'w', encoding='utf-8').close()
            except PermissionError:
                main_logger.warning("Unable to clear log file due to permission error.")

        if on_status_change:
            on_status_change("Initializing browser...", False)

        # initiate Browser
        browser = open_tv.Browser(True, SCREENER_SHORT, SCREENER_NAME, DRAWER_SHORT, DRAWER_NAME, INTERVAL_MINUTES, START_FRESH, SCREENER_OB_SHORT, SCREENER_OB_NAME, SCREENER_NW_SHORT, SCREENER_NW_NAME, SCREENER_SB_SHORT, SCREENER_SB_NAME)

        # setup the indicators, alerts etc.
        setup_check = browser.setup_tv()

        # set up alerts for all the symbols
        if START_FRESH and setup_check:
            browser.set_bulk_alerts()

        if setup_check and browser.init_succeeded:
            if on_status_change:
                on_status_change("Running - monitoring for alerts...", False)

            last_run = time_module.time()
            exits = get_exits.Exits(browser.alerts.local_db, browser.open_chart, browser)
            while True:
                # restart all the inactive alerts every INTERVAL_MINUTES minutes (this is also done in get_alert_data.py in the method get_alert_box_and_msg()) and refresh browser
                if time_module.time() - last_run > interval_seconds:
                    browser.alerts.restart_inactive_alerts()
                    last_run = time_module.time()

                exits.delete_all_get_exits_alerts()

                # do the setup again so that posting of the entries can happen
                if browser.re_setup():
                    # get entries from the alerts which come and post them
                    browser.alerts.post_entries(browser.indicator_visibility)

                # check for exits
                if exits.set_up():
                    exits.check_exits()
        else:
            raise Exception("Failed to initialize TradingView setup")

    except Exception as e:
        main_logger.exception(f'Error in main.py:')
        if on_status_change:
            on_status_change(str(e), True)
        raise

# Run main code if script is run directly
if __name__ == '__main__':
    run_trading_view()
