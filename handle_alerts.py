"""
TradingView to Everywhere (TTE) - Alert Handler Module

Purpose: This module is responsible for handling TradingView alerts and processing the alert messages to extract trading signals.

Functionality: This module provides comprehensive alert handling capabilities:
1. Monitors the TradingView "Alerts log" for new alert messages
2. Extracts trading signal information from alert messages (symbol, entry price, timeframe, take profits, stop loss)
3. Navigates to the relevant chart and applies trade information to the Trade Drawer indicator
4. Captures screenshots of trade entry points
5. Distributes trade information and screenshots to multiple platforms (Discord, MongoDB, external APIs)
6. Manages alerts, including removing processed alerts and restarting inactive alerts
7. Provides specialized handling for exit alerts

Dependencies:
- resources/utils.py: For utility functions
- logger_setup.py: For application logging
- open_entry_chart.py: For chart navigation and manipulation
- resources/symbol_settings.py: For symbol categorization
- send_to_socials/discord.py: For Discord message distribution
- database modules (local_db.py, nk_db.py): For data storage and retrieval
- Selenium WebDriver: For browser interaction
- env.py: For environment variables and configuration

Usage: This module is primarily used by the open_tv.py module, which creates an instance of the Alerts class
and calls its methods to process alerts and distribute trading signals.
"""

from resources.utils import Utils
import logger_setup
import open_entry_chart
from datetime import datetime
from resources.symbol_settings import symbol_category
import send_to_socials.discord as discord
import database.nk_db as nk_db
import database.local_db as db
from time import sleep, time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from json import loads

# Set up logger for this file
alert_data_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

# class
class Alerts:

    def __init__(
        self,
        drawer_shorttitle,
        screener_shorttitles,
        driver,
        chart_timeframe,
        interval_seconds,
    ) -> None:
        self.driver = driver
        self.local_db = db.Database()
        self.nk_db = nk_db.Post()
        self.chart = open_entry_chart.OpenChart(self.driver)
        self.discord = discord.Discord()
        self.drawer_shorttitle = drawer_shorttitle
        self.utils = Utils()
        self.screener_shorttitles = screener_shorttitles
        self.chart_timeframe = chart_timeframe
        self.interval_seconds = interval_seconds
        self.last_run = time()

    def post(self, alert_msg, screener_visibility):
        """This goes through every entry in `alert_msg` and takes a snapshot of those entries and stores them in MongoDB"""
        try:
            # hide all screener indicators with the passed in function (to prevent the screener indicators from showing up in the screenshots)
            for screener_shorttitle in self.screener_shorttitles:
                if not screener_visibility(False, screener_shorttitle):
                    alert_data_logger.warning(
                        f"Failed to hide the screener indicator {screener_shorttitle} but still continuing to post about entries"
                    )

            for (
                key,
                entry_object,
            ) in alert_msg.items():  # go over every json field in this specific alert message
                try:
                    # get all the data from the message
                    screener_type = entry_object["screener"]
                    symbol = entry_object["symbol"]
                    timeframe = entry_object["timeframe"]

                    # go to that specific entry's symbol and its timeframe. Then it inputs all the entry info into the Trade Drawer indicator
                    if not self.chart.change_symbol(symbol):
                        alert_data_logger.error(
                            f"Error in changing the symbol to {symbol}. Going to next symbol."
                        )
                        continue

                    if not self.chart.change_tframe(timeframe):
                        alert_data_logger.error(
                            f"Error in changing the timeframe to {timeframe}. Going to next symbol."
                        )
                        continue

                    if not self.chart.change_indicator_settings(
                        self.drawer_shorttitle,
                        screener_type,
                        entry_object
                    ):
                        alert_data_logger.error(
                            "Error in changing the Trade Drawer indicator's settings. Going to next symbol. "
                        )
                        continue

                    # Take a snapshot of it and send it to social media
                    if not self.send_everywhere(
                        symbol=symbol,
                        timeframe=timeframe,
                        direction=entry_object.get("direction"),
                        screener=entry_object.get("screener"),
                        timestamp=entry_object.get("timestamp"),
                        info=entry_object.get("info")
                    ):
                        alert_data_logger.error(
                            f"Error in sending the entry to all platforms. Going to next symbol."
                        )
                        continue

                except Exception as e:
                    alert_data_logger.exception(
                        f"Error in posting an entry. Continuing to next entry. Error:"
                    )
                    continue

        except Exception as e:
            alert_data_logger.exception(
                "Error in posting an entry. Continuing to next entry. Error:"
            )

    def send_everywhere(self, **kwargs):
        """
        This sends posts to a MongoDB database.
        """
        try:
            # Extracting necessary parameters from kwargs
            symbol = kwargs.get('symbol')
            timeframe = kwargs.get('timeframe')
            direction = kwargs.get('direction')
            screener = kwargs.get('screener')
            timestamp = kwargs.get('timestamp')
            info = kwargs.get('info')
            
            png_link, tv_link = '', ''
            links = self.chart.save_chart_img() 
            if links:
                png_link, tv_link = links['png'], links['tv'] 

            category = symbol_category(symbol)

            # My database
            self.local_db.add_doc(
                {
                    "direction": direction,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "screener": screener,
                    "timestamp": timestamp,
                    "info": info,
                    "tvEntrySnapshot": tv_link,
                    "pngEntrySnapshot": png_link,
                    "category": category,
                }
            )

            # Log success
            alert_data_logger.info(f"Successfully sent entry data to all platforms for symbol {symbol}.")
            return True
        except Exception as e:
            alert_data_logger.error(f"Error sending entry data: {e}")
            return False

    def post_entries(self, screener_visibility):
        '''This goes through all the alerts in the Alerts log and posts each entry that came until all the alerts have been read.'''
        try:
            self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open
            alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
            while alert_boxes:
                alert_msg = self.get_alert()
                self.post(alert_msg, screener_visibility)
                self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open
                alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
        except TimeoutException:
            alert_data_logger.warning('Timeout exception occurred. Assuming that there are no alert boxes.')

    def restart_inactive_alerts(self):
        '''Restarts all the inactive alerts by going to the settings and clicking on "Restart all inactive". Then it will click "Yes" on the popup which comes to confirm the restarting of the alerts.'''
        try:
            # Make sure that the Alerts tab is open
            self.utils.open_alert_tab(self.driver)

            # click the 3 dots
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))).click()

            # wait for the dropdown to show up
            dropdown = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]')))

            # check if the "Show Alerts" section is minimised. if it is, maximise it
            show_all_section = dropdown.find_element(By.CSS_SELECTOR, 'div[class="section-xZRtm41u summary-ynHBVe1n"]')
            maximized = True if show_all_section.get_attribute('data-open') == 'true' else False
            if not maximized:
                show_all_section.click()
                alert_data_logger.info('Maximized the "Show Alerts" section')

            # then check if the "All" option is selected. if it is not, select it
            all_option = dropdown.find_element(By.CSS_SELECTOR, 'div[class="item-xZRtm41u item-jFqVJoPk"]')
            if not all_option.find_element(By.TAG_NAME, 'input').is_selected():
                all_option.click()
                alert_data_logger.info('Selected the "All" option')

            # then click on "Restart all inactive"
            dropdown_button = dropdown.find_element(By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')
            if dropdown_button.text == 'Restart all inactive':
                dropdown_button.click()
                alert_data_logger.info('Clicked on "Restart all inactive"')

                # click Yes when the popup comes
                popup = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]')))
                popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
                alert_data_logger.info('Restarting all inactive alerts!')

            sleep(1)
            return True
        except Exception as e:
            alert_data_logger.exception('Error occurred when restarting the inactive alerts. Error:')
            return False

    def get_alert(self):
        '''Whenever it sees an alert in the Logs tab, the alert gets deleted from the log and its message gets returned'''
        try:
            alert_box, alert_msg = self.get_alert_box_and_msg()
            if alert_box and alert_msg:
                if self.remove_alert(alert_box):
                    return loads(alert_msg) if alert_msg != None else loads('{}')# the alert message is jsonified

        except StaleElementReferenceException:
            alert_data_logger.error('StaleElementReferenceException while reading the alert. Trying again to get alert...')
            alert_box, alert_msg = self.get_alert_box_and_msg()
            if alert_box and alert_msg:
                if self.remove_alert(alert_box):
                    return loads(alert_msg) if alert_msg != None else loads('{}')# the alert message is jsonified

        except Exception as e:
            alert_data_logger.exception('Error in reading the alert. Error:')
            return loads('{}')

    def get_alert_box_and_msg(self):
        '''Returns the last alert box and its message if there is an alert. If there is no alert, it waits for one. Also, it restarts all the inactive alerts periodically. If something goes wrong, `None, None` gets returned'''
        try:
            # restart all the inactive alerts every INTERVAL_MINUTES minutes (this is also done in get_alert_data.py in the method get_alert_box_and_msg())
            if time() - self.last_run > self.interval_seconds:
                self.restart_inactive_alerts()
                self.last_run = time()

            self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open
            alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
            if alert_boxes:
                alert_box = alert_boxes[-1] # take the last alert (the oldest one)
                alert_msg = alert_box.find_element(By.CSS_SELECTOR, 'div[class="message-PQUvhamm"]').text 
                if not alert_box.is_displayed() and not self.scroll_to_alert(alert_box):
                    alert_data_logger.error('Failed to scroll to alert')
                    return loads('{}'), loads('{}')
                return alert_box, alert_msg
            return loads('{}'), loads('{}')
        except TimeoutException:
            alert_data_logger.error('TimeoutException occured while waiting for an alert.')
            return loads('{}'), loads('{}')
        except Exception as e:
            alert_data_logger.exception('Error in getting the alert box and message. Error:')
            return loads('{}'), loads('{}')

    def remove_alert(self, alert_box):
        '''Removes the alert from the Alert log by clicking on the alert message and using Shift+Delete'''
        try:
            self.utils.open_log_tab(self.driver) # Make sure that the Logs tab is open
            
            # Click on the alert message to select it
            alert_box.click()
            
            # Use Shift+Delete keyboard shortcut to remove the alert
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.DELETE).key_up(Keys.SHIFT).perform()
            sleep(0.5)

            alert_data_logger.info('Successfully removed alert using Shift+Delete')
            return True
        except Exception as e:
            alert_data_logger.exception('Error in removing the alert from the Alert log. Error:')
            return False

    def scroll_to_alert(self, alert):
        '''This scrolls to the given alert'''
        try:
            self.driver.execute_script("arguments[0].scrollIntoView();", alert)
            sleep(0.7)
            return True
        except Exception as e:
            alert_data_logger.exception('Error in scrolling to the alert. Error:')
            return False
