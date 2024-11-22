'''
A class that contains commonly used methods.
'''

from time import sleep
import logger_setup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

# Set up a logger for this file
utils_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

class Utils:
    def is_log_tab_open(self, driver):
        '''
        This checks if the Logs tab is open or not. If it is open, it returns True. If it is not open or an error occurs, it returns False.
        '''
        try:
            # make sure the the Alerts tab is currently open
            alert_tab_selector = 'div[class="widget-X9EuSe_t widgetbar-widget widgetbar-widget-alerts"] div[class="widgetHeader-X9EuSe_t"] div[id="AlertsHeaderTabs"] button[data-name="light-tab-1"]'

            if WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, alert_tab_selector))).get_attribute('aria-selected') == 'true': # if the Alerts tab is already open
                utils_logger.info('Logs tab is already open.')
                return True
            else: # if the Alerts tab is not open, open it
                utils_logger.info('Logs tab is closed.')
                return False
        
        except Exception as e:
            utils_logger.exception(f'Error ocurred when opening the Alert tab. Error: ')
            return False

    def is_alert_tab_open(self, driver):
        '''
        This checks if the Alerts tab is open or not. If it is open, it returns True. If it is not open or an error occurs, it returns False.
        '''
        try:
            # make sure the the Alerts tab is currently open
            alert_tab_selector = 'div[class="widget-X9EuSe_t widgetbar-widget widgetbar-widget-alerts"] div[class="widgetHeader-X9EuSe_t"] div[id="AlertsHeaderTabs"] button[data-name="light-tab-0"]'

            if WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, alert_tab_selector))).get_attribute('aria-selected') == 'true': # if the Alerts tab is already open
                utils_logger.info('Alerts tab is already open.')
                return True
            else: # if the Alerts tab is not open, open it
                utils_logger.info('Alerts tab is closed.')
                return False
        
        except Exception as e:
            utils_logger.exception(f'Error ocurred when opening the Alert tab. Error: ')
            return False

    def open_alert_tab(self, driver):
        '''
        This makes sure that the Alert tab in the alerts sidebar is open. If it isn't, it opens the Alerts tab.

        Args:
        - driver: The Selenium WebDriver instance
        '''
        try:
            # make sure the the Alerts tab is currently open
            alert_tab_selector = 'div[class="widget-X9EuSe_t widgetbar-widget widgetbar-widget-alerts"] div[class="widgetHeader-X9EuSe_t"] div[id="AlertsHeaderTabs"] button[data-name="light-tab-0"]'

            if WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, alert_tab_selector))).get_attribute('aria-selected') == 'true': # if the Alerts tab is already open
                utils_logger.info('Alerts tab is already open. No need to open it!')
            else: # if the Alerts tab is not open, open it
                utils_logger.info('Alerts tab is closed. Will open it.')
                WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, alert_tab_selector))).click() # open the Alerts tab
            
            # Wait until the Alerts tab opens
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alert-item-name"]')))
            return True
        except Exception as e:
            utils_logger.exception(f'Error ocurred when opening the Alert tab. Error: ')
            return False
        
    def open_log_tab(self, driver):
        '''This makes sure that the Log tab in the alerts sidebar is open.'''
        try:
            # make sure the the Log tab is currently open
            alert_tab_selector = 'div[class="widget-X9EuSe_t widgetbar-widget widgetbar-widget-alerts"] div[class="widgetHeader-X9EuSe_t"] div[id="AlertsHeaderTabs"] button[data-name="light-tab-1"]'

            if driver.find_element(By.CSS_SELECTOR, alert_tab_selector).get_attribute('aria-selected') == 'true': # if the Log tab is already open
                utils_logger.info('Log tab is already open. No need to open it!')
            else: # if the Log tab is not open, open it
                utils_logger.info('Logs tab is closed. Will open it.')
                WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, alert_tab_selector))).click() # open the Log tab
            
            # Wait until the Logs tab opens
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
            return True
        except Exception as e:
            utils_logger.exception(f'Error occurred when opening the Log tab. Error: ')
            return False

    def click_yes_in_confirm_popup(self, driver):
        '''This clicks the Yes button in the confirmation popup that appears on TradingView.'''
        try:
            dialog = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="confirm-dialog"]')))
            WebDriverWait(dialog, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="yes"]'))).click()
            sleep(2)
            return True
        except Exception as e:
            utils_logger.exception(f'Error occurred when clicking the Yes button in the confirmation popup. Error: ')
            return False
