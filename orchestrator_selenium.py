"""
Selenium Browser Automation for TTE Orchestrator.

Manages Chrome browser automation for:
- Updating symbol inputs in NWE and OBDIV screener indicators
- Creating webhook alerts for TradingView indicators
- Navigating TradingView charts and changing timeframes
- Pausing existing alerts before creating new ones (safer than delete)

This module merges battle-tested patterns from:
- selenium_manager.py (driver init, indicator settings, alerts)
- open_entry_chart.py (symbol/timeframe changes)
- resources/utils.py (confirmation popups)
"""

import os
import time
import functools
from typing import List, Optional, Callable, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
    StaleElementReferenceException
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import read_version_from_cmd
from webdriver_manager.core.os_manager import PATTERN

from config import config
from utils.logger import get_logger

logger = get_logger('orchestrator_selenium')


class SeleniumError(Exception):
    """Raised when Selenium operations fail."""
    pass


def retry_on_failure(max_retries: int = 3, delay: float = 2.0,
                     exceptions: tuple = (TimeoutException, StaleElementReferenceException)):
    """
    Decorator to retry a method on specific exceptions.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exception types to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")
            raise last_exception
        return wrapper
    return decorator


# ============================================
# TradingView Selector Constants
# ============================================

class TVSelectors:
    """TradingView UI selectors - VERIFIED 2026-01-30 via manual inspection."""

    # Legend / Indicator (FIXED: data-qa-id instead of data-name)
    LEGEND_ITEM = 'div[data-qa-id="legend-source-item"]'
    INDICATOR_TITLE = 'div[class*="title"]'
    INDICATOR_SETTINGS_DIALOG = '[data-dialog-name="indicatorSettings"], .tv-dialog--indicator-properties'

    # Alert Dialog - VERIFIED 2026-01-30
    SET_ALERT_BUTTON = 'div[data-name="set-alert-button"]'
    ALERT_DIALOG = 'div[data-qa-id="alerts-create-edit-dialog"]'
    ALERT_NAME_INPUT = 'input[id="alert-name"]'
    ALERT_ERROR_HINT = 'div[data-name="error-hint"]'

    # Settings Tab - Condition Dropdown (1st dropdown in Settings tab)
    CONDITION_DROPDOWN = 'span[data-qa-id="ui-kit-disclosure-control main-series-select"]'
    DROPDOWN_MENU = 'div[data-qa-id="ui-kit-disclosure-popup popup-menu-container main-series-select"]'
    MENU_ITEMS = 'div[role="option"]'

    # Alert Dialog Tabs - VERIFIED 2026-01-30
    SETTINGS_TAB = '#alert-dialog-tabs__settings'
    NOTIFICATIONS_TAB = '#alert-dialog-tabs__notifications'
    MESSAGE_TAB = '#alert-dialog-tabs__message'

    # Webhook Configuration (in Notifications tab) - VERIFIED 2026-01-30
    WEBHOOK_CHECKBOX = 'input[data-qa-id="webhook"]'
    WEBHOOK_URL_INPUT = '#webhook-url'

    # Buttons - VERIFIED 2026-01-30
    SUBMIT_BUTTON = 'button[data-qa-id="submit"]'
    APPLY_BUTTON = 'button[data-name="apply"]'
    CANCEL_BUTTON = 'button[data-qa-id="cancel"]'
    CLOSE_BUTTON = 'button[data-name="close"]'
    OK_BUTTON_XPATH = "//button[contains(text(), 'OK')]"

    # Chart
    CHART_CONTAINER = '.chart-container'

    # Alerts Settings (FIXED: data-name for MENU_INNER - verified via main/point-capital branches)
    ALERTS_SETTINGS_BUTTON = 'div[data-name="alerts-settings-button"]'
    MENU_INNER = 'div[data-name="menu-inner"]'

    # Confirmation Dialog
    CONFIRM_DIALOG = 'div[data-name="confirm-dialog"]'
    CONFIRM_YES_BUTTON = 'button[name="yes"]'


class OrchestratorSelenium:
    """
    Manages browser automation for TradingView interactions.

    Handles:
    - Chrome driver lifecycle
    - TradingView chart navigation
    - Symbol and timeframe changes
    - Indicator settings modification
    - Alert creation and deletion
    """

    def __init__(self):
        """Initialize the orchestrator selenium manager."""
        self.driver: Optional[webdriver.Chrome] = None

    def _init_driver(self) -> webdriver.Chrome:
        """
        Initialize Chrome driver instance.

        Uses the same approach as the working open_tv.py:
        - Separate TTE profile folder
        - Chrome version detection via PowerShell
        - Remote debugging port 9224

        Returns:
            Chrome WebDriver instance
        """
        if self.driver is not None:
            return self.driver

        logger.info("Initializing Chrome driver...")

        chrome_options = Options()

        # Use the same profile setup as open_tv.py
        chrome_profiles_path = config.CHROME_PROFILES_PATH or os.getenv(
            "CHROME_PROFILES_PATH",
            "C:/Users/dassa/AppData/Local/Google/Chrome/User Data"
        )
        profile_name = config.CHROME_PROFILE_NAME or os.getenv("CHROME_PROFILE_NAME", "Profile 3")

        # Key settings from working open_tv.py
        chrome_options.add_argument(f"--profile-directory={profile_name}")
        chrome_options.add_argument(f"--user-data-dir={chrome_profiles_path}/TTE")
        chrome_options.add_argument("--remote-debugging-port=9224")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Keep browser open after script ends (for debugging)
        chrome_options.add_experimental_option("detach", True)

        try:
            # Get Chrome version using PowerShell (same as open_tv.py)
            cmd = 'powershell -command "&{(Get-Item \'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\').VersionInfo.ProductVersion}"'
            try:
                version = read_version_from_cmd(cmd, PATTERN["google-chrome"])
                logger.info(f"Detected Chrome version: {version}")
                service_path = ChromeDriverManager(driver_version=version).install()
            except Exception as e:
                logger.warning(f"Could not detect Chrome version: {e}. Using auto-detection.")
                service_path = ChromeDriverManager().install()

            self.driver = webdriver.Chrome(
                service=ChromeService(service_path),
                options=chrome_options
            )

            # Configure timeouts
            self.driver.implicitly_wait(config.SELENIUM_IMPLICIT_WAIT)
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)

            # Maximize window
            self.driver.maximize_window()

            logger.info("Chrome driver initialized successfully")

        except WebDriverException as e:
            error_msg = str(e)
            logger.error(f"Failed to initialize Chrome driver: {e}")

            # Provide helpful error message
            if "DevToolsActivePort" in error_msg or "session not created" in error_msg or "chrome not reachable" in error_msg:
                raise SeleniumError(
                    "Chrome driver initialization failed.\n\n"
                    "This usually means Chrome is already running with the TTE profile.\n"
                    "Please:\n"
                    "  1. Close ALL Chrome windows completely\n"
                    "  2. Check Task Manager and end any chrome.exe processes\n"
                    "  3. Try again\n\n"
                    f"Original error: {e}"
                )
            else:
                raise SeleniumError(f"Chrome driver initialization failed: {e}")

        return self.driver

    def get_driver(self) -> webdriver.Chrome:
        """Get or create Chrome driver instance."""
        if self.driver is None:
            return self._init_driver()
        return self.driver

    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome driver closed")
            except Exception as e:
                logger.warning(f"Error closing Chrome driver: {e}")
            finally:
                self.driver = None

    def _check_login_required(self) -> bool:
        """
        Check if TradingView login is required.

        Returns:
            True if login is required, False if already logged in
        """
        driver = self.get_driver()

        try:
            # Look for signs we're NOT logged in
            login_indicators = [
                "//button[contains(text(), 'Sign in')]",
                "//button[contains(text(), 'Log in')]",
                "//a[contains(@href, '/signin')]",
                "//div[contains(@class, 'tv-header__login')]"
            ]

            for indicator in login_indicators:
                try:
                    element = driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue

            # Also check if we're on a login page
            current_url = driver.current_url.lower()
            if 'signin' in current_url or 'login' in current_url:
                return True

            return False

        except Exception as e:
            logger.warning(f"Could not check login status: {e}")
            return False  # Assume logged in if check fails

    @retry_on_failure(max_retries=2, delay=2.0)
    def navigate_to_chart(self, url: str, wait_time: float = 5.0, wait_for_chart: bool = True):
        """
        Navigate to a TradingView chart.

        Args:
            url: Full URL to the chart
            wait_time: Seconds to wait for chart to load
            wait_for_chart: If True, wait for chart container to be present.
        """
        driver = self.get_driver()
        logger.info(f"Navigating to: {url}")

        try:
            driver.get(url)
            time.sleep(wait_time)

            # Check if we're logged in
            if self._check_login_required():
                logger.error("TradingView login required! Please log in manually.")
                raise SeleniumError(
                    "TradingView login required. Please open Chrome manually, "
                    "log into TradingView, then restart the orchestrator."
                )

            if wait_for_chart:
                # Wait for chart container to be present
                WebDriverWait(driver, config.SELENIUM_EXPLICIT_WAIT).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "chart-container"))
                )
                logger.debug("Chart loaded successfully")

        except TimeoutException:
            logger.warning("Chart container not found, continuing anyway")
        except WebDriverException as e:
            logger.error(f"Navigation failed: {e}")
            raise SeleniumError(f"Failed to navigate to chart: {e}")

    def change_tframe(self, timeframe: str) -> bool:
        """
        Change the timeframe of the chart.

        Based on open_entry_chart.py:257-306

        Args:
            timeframe: Timeframe label (e.g., "4 hours", "1 day", "1 week")

        Returns:
            True if successful, False otherwise
        """
        driver = self.get_driver()

        try:
            # Click on the timeframe dropdown
            tf_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="header-toolbar-intervals"]/button')
                )
            )

            # If the chart's timeframe is already the desired one, skip
            if tf_button.get_attribute("aria-label") == timeframe:
                logger.info(f"Timeframe already set to {timeframe}, no change needed")
                return True

            # Click to open dropdown
            tf_button.click()

            # Wait for dropdown to appear
            options_container = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[class="dropdown-S_1OCXUK"]')
                )
            )

            # Find all menu items
            options = options_container.find_elements(
                By.CSS_SELECTOR,
                'div[class="accessible-NQERJsv9 menuItem-RmqZNwwp item-jFqVJoPk"]'
            )

            # Find and click the matching option
            for option in options:
                try:
                    label = option.find_element(
                        By.CSS_SELECTOR, 'span[class="label-jFqVJoPk"]'
                    ).text
                    if label == timeframe:
                        option.click()
                        logger.info(f"Changed timeframe to {timeframe}")
                        time.sleep(1)  # Wait for chart to update
                        return True
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            logger.warning(f"Timeframe option '{timeframe}' not found in dropdown")
            # Press Escape to close dropdown
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return False

        except TimeoutException as e:
            logger.error(f"Timeout changing timeframe to {timeframe}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Failed to change timeframe to {timeframe}")
            return False

    def change_symbol(self, symbol: str) -> bool:
        """
        Change the chart's symbol.

        Based on open_entry_chart.py:207-255

        Args:
            symbol: Symbol to change to (e.g., "EURUSD", "NSE:RELIANCE")

        Returns:
            True if successful, False otherwise
        """
        driver = self.get_driver()

        try:
            # Get symbol without exchange prefix for comparison
            no_exchange_symbol = symbol.split(":")[-1] if ":" in symbol else symbol

            # Find symbol search button
            symbol_search = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"]')
                )
            )

            # Check if current symbol matches
            current_symbol = symbol_search.find_element(By.CSS_SELECTOR, "div").text
            if current_symbol == no_exchange_symbol:
                logger.info(f"Symbol already set to {no_exchange_symbol}, no change needed")
                return True

            # Click to open search
            symbol_search.click()

            # Find search input
            search_input = driver.find_element(
                By.XPATH,
                '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div[2]/div[1]/input'
            )

            # Clear existing text using Ctrl+A pattern
            ActionChains(driver).key_down(Keys.CONTROL, search_input).send_keys("a").perform()
            search_input.send_keys(Keys.DELETE)

            # Enter symbol and press Enter
            search_input.send_keys(symbol)
            search_input.send_keys(Keys.ENTER)

            logger.info(f"Entered symbol {symbol}")

            # Wait for symbol to change
            WebDriverWait(driver, 5).until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"] div'),
                    no_exchange_symbol,
                )
            )

            time.sleep(1.5)  # Wait for chart to load
            return True

        except TimeoutException as e:
            logger.error(f"Timeout changing symbol to {symbol}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Failed to change symbol to {symbol}")
            return False

    @retry_on_failure(max_retries=3, delay=1.0)
    def open_indicator_settings(self, indicator_name: str):
        """
        Open settings dialog for an indicator.

        Based on open_tv.py - click indicator then click settings button.
        Uses partial matching as fallback if exact match fails.

        Args:
            indicator_name: Name of the indicator as shown in legend

        Raises:
            SeleniumError: If indicator not found or settings can't be opened
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, config.SELENIUM_EXPLICIT_WAIT)

        # Selectors from open_tv.py
        LEGEND_SETTINGS_BUTTON = 'button[data-name="legend-settings-action"]'
        SETTINGS_CONTENT = '.content-tBgV1m0B'

        try:
            logger.info(f"Opening settings for indicator: '{indicator_name}'")

            # Find all legend items
            logger.debug(f"Looking for legend items with selector: {TVSelectors.LEGEND_ITEM}")
            indicators = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, TVSelectors.LEGEND_ITEM)
                )
            )
            logger.debug(f"Found {len(indicators)} legend items")

            # Collect all indicator names for logging
            found_names = []
            for ind in indicators:
                try:
                    title = ind.find_element(
                        By.CSS_SELECTOR, TVSelectors.INDICATOR_TITLE
                    ).text.strip()
                    found_names.append(title)
                except (NoSuchElementException, StaleElementReferenceException):
                    found_names.append("(unreadable)")

            logger.debug(f"Indicator names found in legend: {found_names}")

            # First pass: exact match
            indicator_element = None
            for i, ind in enumerate(indicators):
                try:
                    title = found_names[i]
                    if title == indicator_name:
                        logger.info(f"Found exact match: '{title}'")
                        indicator_element = ind
                        break
                except (IndexError, StaleElementReferenceException):
                    continue

            # Second pass: partial match (case-insensitive)
            if not indicator_element:
                logger.debug(f"No exact match, trying partial match for '{indicator_name}'...")
                search_term = indicator_name.lower()
                for i, ind in enumerate(indicators):
                    try:
                        title = found_names[i]
                        if search_term in title.lower():
                            logger.info(f"Found partial match: '{title}'")
                            indicator_element = ind
                            break
                    except (IndexError, StaleElementReferenceException):
                        continue

            if not indicator_element:
                logger.error(f"Indicator not found: '{indicator_name}'")
                logger.error(f"Available indicators: {found_names}")
                raise SeleniumError(f"Indicator not found: {indicator_name}")

            # Step 1: Click on the indicator to select it
            logger.debug("Step 1: Clicking on indicator to select it...")
            indicator_element.click()
            time.sleep(0.3)

            # Step 2: Click the settings button (gear icon)
            logger.debug("Step 2: Looking for settings button (gear icon)...")
            settings_button = WebDriverWait(indicator_element, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, LEGEND_SETTINGS_BUTTON))
            )
            logger.debug("Found settings button, clicking...")
            settings_button.click()

            # Step 3: Wait for settings dialog to appear
            logger.debug("Step 3: Waiting for settings dialog...")
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SETTINGS_CONTENT))
            )

            logger.info(f"Successfully opened settings for: {indicator_name}")
            time.sleep(0.5)  # Brief pause for dialog animation

        except TimeoutException:
            logger.error(f"Timeout: Could not find or open settings for: {indicator_name}")
            raise SeleniumError(f"Indicator not found: {indicator_name}")

    def set_symbol_inputs(self, symbols: List[str], max_inputs: int = 40):
        """
        Set symbol input fields in indicator settings dialog.

        Based on point-capital branch open_tv.py - uses edit buttons and symbol search popup.

        Args:
            symbols: List of symbols to set
            max_inputs: Maximum number of input fields to set
        """
        driver = self.get_driver()

        # Selectors from point-capital branch
        SETTINGS_CONTENT = '.content-tBgV1m0B'
        SYMBOL_EDIT_BUTTONS = '.inlineRow-tBgV1m0B div[data-name="edit-button"]'
        SYMBOL_SEARCH_INPUT = '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input'

        try:
            # Find the settings content area
            settings = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SETTINGS_CONTENT))
            )

            # Find all symbol edit buttons
            symbol_edit_buttons = settings.find_elements(By.CSS_SELECTOR, SYMBOL_EDIT_BUTTONS)
            logger.info(f"Found {len(symbol_edit_buttons)} symbol edit buttons")

            if not symbol_edit_buttons:
                raise SeleniumError("No symbol edit buttons found in settings dialog")

            # Set each symbol by clicking edit button and using search popup
            symbols_to_set = symbols[:min(len(symbols), len(symbol_edit_buttons), max_inputs)]

            for i, symbol in enumerate(symbols_to_set):
                try:
                    edit_button = symbol_edit_buttons[i]

                    # Scroll into view to prevent click interception
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        edit_button
                    )
                    time.sleep(0.3)

                    # Use ActionChains for reliable clicking (prevents interception)
                    ActionChains(driver).move_to_element(edit_button).click().perform()
                    time.sleep(0.3)

                    # Find the search input
                    search_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, SYMBOL_SEARCH_INPUT))
                    )

                    # Clear with Ctrl+A/Delete (more reliable than .clear())
                    ActionChains(driver).key_down(Keys.CONTROL, search_input).send_keys('a').key_up(Keys.CONTROL).perform()
                    search_input.send_keys(Keys.DELETE)
                    time.sleep(0.1)

                    # Type symbol and submit
                    search_input.send_keys(symbol)
                    search_input.send_keys(Keys.ENTER)
                    time.sleep(0.3)

                    logger.debug(f"Set symbol {i + 1} to: {symbol}")

                except (TimeoutException, StaleElementReferenceException) as e:
                    logger.warning(f"Failed to set symbol {i + 1} ({symbol}): {e}")
                    # Try to close any open popup by pressing Escape
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(0.2)
                    continue

            logger.info(f"Set {len(symbols_to_set)} symbol inputs")

        except NoSuchElementException as e:
            logger.error(f"Could not find symbol inputs: {e}")
            raise SeleniumError("Symbol inputs not found in settings dialog")
        except TimeoutException as e:
            logger.error(f"Timeout finding settings content: {e}")
            raise SeleniumError("Settings dialog not found")

    def click_ok_button(self, wait_for_recalc: bool = True):
        """
        Click OK/Apply button to save indicator settings.

        Args:
            wait_for_recalc: If True, wait 10 seconds for indicator to recalculate.

        Raises:
            SeleniumError: If button not found
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, config.SELENIUM_EXPLICIT_WAIT)

        try:
            button_selectors = [
                "button[name='submit']",  # point-capital selector
                "button[data-name='submit']",
                "button[data-name='apply']",
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Apply')]",
                ".tv-dialog__submit-button"
            ]

            button = None
            for selector in button_selectors:
                try:
                    if selector.startswith('//'):
                        button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        button = wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    break
                except TimeoutException:
                    continue

            if button:
                button.click()
                logger.info("Clicked OK/Apply button")
                if wait_for_recalc:
                    # Wait for indicator to recalculate after symbol changes
                    logger.info("Waiting 10 seconds for indicator to recalculate...")
                    time.sleep(10)
                else:
                    time.sleep(2)
            else:
                raise SeleniumError("OK/Apply button not found")

        except TimeoutException:
            logger.error("Could not find OK/Apply button")
            raise SeleniumError("OK/Apply button not found")

    def click_yes_in_confirm_popup(self) -> bool:
        """
        Click the Yes button in TradingView confirmation popup.

        Based on resources/utils.py:141-158

        Returns:
            True if clicked successfully, False otherwise
        """
        driver = self.get_driver()

        try:
            dialog = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, TVSelectors.CONFIRM_DIALOG)
                )
            )
            WebDriverWait(dialog, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.CONFIRM_YES_BUTTON))
            ).click()
            time.sleep(2)
            logger.info("Clicked Yes in confirmation popup")
            return True
        except TimeoutException:
            logger.debug("No confirmation popup found")
            return False
        except Exception as e:
            logger.warning(f"Error clicking Yes in confirmation popup: {e}")
            return False

    def _scroll_to_element(self, element):
        """
        Scroll element into view to prevent click interception.

        Uses smooth scrolling to center the element in the viewport.

        Args:
            element: WebElement to scroll to
        """
        driver = self.get_driver()
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
            element
        )
        time.sleep(0.3)

    def open_alert_tab(self) -> bool:
        """
        Ensure the Alerts tab in the sidebar is open.

        Based on resources/utils.py:74-109

        Returns:
            True if successful, False otherwise
        """
        driver = self.get_driver()

        # Selector for the Alerts tab button
        ALERT_TAB_SELECTOR = 'div[class="widget-X9EuSe_t widgetbar-widget widgetbar-widget-alerts"] div[class="widgetHeader-X9EuSe_t"] div[id="AlertsHeaderTabs"] button[data-name="light-tab-0"]'

        try:
            logger.debug("Checking if Alerts tab is open...")

            alert_tab = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ALERT_TAB_SELECTOR))
            )

            if alert_tab.get_attribute("aria-selected") == "true":
                logger.debug("Alerts tab is already open")
            else:
                logger.debug("Alerts tab is closed, opening it...")
                WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ALERT_TAB_SELECTOR))
                ).click()

            # Wait for tab to be fully open
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "AlertsHeaderTabs"))
            )
            logger.debug("Alerts tab is now open")
            return True

        except TimeoutException:
            logger.warning("Could not find Alerts tab - sidebar may not be visible")
            return False
        except Exception as e:
            logger.error(f"Error opening Alerts tab: {e}")
            return False

    def delete_all_alerts(self) -> bool:
        """
        Delete all alerts in TradingView.

        Based on open_tv.py - the correct 2-step approach:
        1. Open Alerts tab
        2. Open dropdown -> Click "Stop All" -> Confirm popup
        3. Open dropdown -> Click "Delete All Inactive" -> Confirm popup

        Returns:
            True if successful
        """
        driver = self.get_driver()

        # Selectors from open_tv.py
        DROPDOWN_OPTION = 'div.item-jFqVJoPk'
        ALERT_ITEMS = 'div.list-G90Hl2iS div.itemBody-ucBqatk5'

        def open_dropdown():
            """Open the alerts settings dropdown if not already open."""
            logger.debug("Opening alerts settings dropdown...")
            # If dropdown isn't already open, click the 3 dots
            if not driver.find_elements(By.CSS_SELECTOR, TVSelectors.MENU_INNER):
                logger.debug("Dropdown not open, clicking settings button...")
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.ALERTS_SETTINGS_BUTTON))
                ).click()
            dropdown = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, TVSelectors.MENU_INNER))
            )
            logger.debug("Dropdown opened successfully")
            return dropdown

        try:
            logger.info("Starting alert deletion process...")

            # Step 0: Make sure Alerts tab is open
            logger.debug("Step 0: Opening Alerts tab...")
            self.open_alert_tab()

            # Check if there are any alerts first
            time.sleep(1)  # Wait for alerts list to load
            alert_items = driver.find_elements(By.CSS_SELECTOR, ALERT_ITEMS)
            logger.debug(f"Looking for alerts with selector: {ALERT_ITEMS}")

            if not alert_items:
                logger.info("No alerts found. Nothing to delete.")
                return True

            logger.info(f"Found {len(alert_items)} alerts. Proceeding to delete...")

            # Step 1: Open dropdown and click "Stop All" (index 1)
            logger.debug("Step 1: Opening dropdown to click 'Stop All'...")
            dropdown = open_dropdown()
            options = WebDriverWait(dropdown, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, DROPDOWN_OPTION))
            )
            logger.debug(f"Found {len(options)} dropdown options")

            # Log all option texts for debugging
            for i, opt in enumerate(options):
                try:
                    logger.debug(f"  Option [{i}]: '{opt.text}' - class: {opt.get_attribute('class')}")
                except:
                    logger.debug(f"  Option [{i}]: (could not read)")

            # "Stop All" is typically at index 1
            if len(options) > 1:
                stop_all_button = options[1]
                stop_class = stop_all_button.get_attribute('class') or ''
                if 'isDisabled' in stop_class:
                    logger.info('"Stop All" is disabled - alerts may already be stopped')
                else:
                    logger.debug("Clicking 'Stop All' button...")
                    stop_all_button.click()
                    time.sleep(0.5)
                    self.click_yes_in_confirm_popup()
                    logger.info("Clicked 'Stop All' and confirmed")
            else:
                logger.warning("Not enough dropdown options for 'Stop All'")

            # Step 2: Open dropdown again and click "Delete All Inactive" (index 2)
            logger.debug("Step 2: Opening dropdown to click 'Delete All Inactive'...")
            time.sleep(0.5)
            dropdown = open_dropdown()
            options = WebDriverWait(dropdown, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, DROPDOWN_OPTION))
            )

            # "Delete All Inactive" is typically at index 2
            if len(options) > 2:
                delete_inactive_button = options[2]
                delete_class = delete_inactive_button.get_attribute('class') or ''
                if 'isDisabled' in delete_class:
                    logger.info('"Delete All Inactive" is disabled - no inactive alerts')
                else:
                    logger.debug("Clicking 'Delete All Inactive' button...")
                    delete_inactive_button.click()
                    time.sleep(0.5)
                    self.click_yes_in_confirm_popup()
                    logger.info("Clicked 'Delete All Inactive' and confirmed")
            else:
                logger.warning("Not enough dropdown options for 'Delete All Inactive'")

            # Verify deletion
            time.sleep(1)
            remaining_alerts = driver.find_elements(By.CSS_SELECTOR, ALERT_ITEMS)
            if not remaining_alerts:
                logger.info("All alerts deleted successfully!")
                return True
            else:
                logger.warning(f"{len(remaining_alerts)} alerts still remain")
                return True  # Still return True - some alerts deleted

        except TimeoutException as e:
            logger.warning(f"Timeout during alert deletion: {e}")
            return True  # No alerts to delete is still success
        except Exception as e:
            logger.error(f"Failed to delete alerts: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False

    def pause_all_alerts(self) -> bool:
        """
        Pause all active alerts in TradingView.

        Safer than delete - stops alerts without removing them.
        No confirmation popup needed, always available (not disabled).

        Returns:
            True if successful
        """
        driver = self.get_driver()

        # Selectors
        DROPDOWN_OPTION = 'div.item-jFqVJoPk'
        ACTIVE_ALERTS = 'div.itemBody-ucBqatk5.active-Bj96_lIl'

        def open_dropdown():
            """Open the alerts settings dropdown if not already open."""
            if not driver.find_elements(By.CSS_SELECTOR, TVSelectors.MENU_INNER):
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.ALERTS_SETTINGS_BUTTON))
                ).click()
            return WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, TVSelectors.MENU_INNER))
            )

        try:
            logger.info("Starting alert pause process...")

            # Step 0: Open Alerts tab
            self.open_alert_tab()

            # Check for active alerts
            time.sleep(1)
            active_alerts = driver.find_elements(By.CSS_SELECTOR, ACTIVE_ALERTS)

            if not active_alerts:
                logger.info("No active alerts to pause")
                return True

            logger.info(f"Found {len(active_alerts)} active alerts. Pausing...")

            # Open dropdown and click "Pause all" (index 1)
            # Dropdown order: [0] Restart all inactive, [1] Pause all, [2] Delete all inactive
            dropdown = open_dropdown()
            options = WebDriverWait(dropdown, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, DROPDOWN_OPTION))
            )

            if len(options) > 1:
                pause_button = options[1]
                pause_class = pause_button.get_attribute('class') or ''
                if 'isDisabled' in pause_class:
                    logger.info('"Pause all" is disabled - no active alerts')
                else:
                    pause_button.click()
                    logger.info("Clicked 'Pause all'")
                    time.sleep(1)

            logger.info("All alerts paused successfully!")
            return True

        except TimeoutException:
            logger.warning("Timeout during alert pausing")
            return True  # Not fatal
        except Exception as e:
            logger.error(f"Failed to pause alerts: {e}")
            return False

    @retry_on_failure(max_retries=2, delay=1.0)
    def create_webhook_alert(
        self,
        indicator_name: str,
        webhook_url: str,
        alert_name: str = "TTE Webhook"
    ) -> bool:
        """
        Create a TradingView alert with webhook configuration.

        Based on selenium_manager.py:611-789 plus 2s wait at end.

        Steps:
        1. Click Set Alert button (+)
        2. Wait for dialog
        3. Settings tab: Select indicator from condition dropdown
        4. Notifications tab: Enable webhook, enter URL
        5. Click Create
        6. Wait 2 seconds for completion

        Args:
            indicator_name: Short title of the indicator (as shown in legend)
            webhook_url: URL to send webhook POST requests to
            alert_name: Name for the alert (default: "TTE Webhook")

        Returns:
            True if alert was created successfully

        Raises:
            SeleniumError: If alert creation fails
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, config.SELENIUM_EXPLICIT_WAIT)

        try:
            # Step 1: Click Set Alert button (+)
            logger.info(f"Step 1: Clicking Set Alert button for: {indicator_name}")
            alert_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.SET_ALERT_BUTTON))
            )
            alert_btn.click()
            time.sleep(1)

            # Step 2: Wait for alert dialog
            logger.info("Step 2: Waiting for alert dialog...")
            dialog = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, TVSelectors.ALERT_DIALOG))
            )
            time.sleep(0.5)

            # Step 3: Settings tab - Select indicator from condition dropdown
            logger.info(f"Step 3: Selecting indicator '{indicator_name}' from condition dropdown...")

            # Click the condition dropdown
            condition_dropdown = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.CONDITION_DROPDOWN))
            )
            condition_dropdown.click()
            time.sleep(0.5)

            # Wait for dropdown menu to appear
            dropdown_menu = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, TVSelectors.DROPDOWN_MENU))
            )

            # Find all menu items
            menu_items = dropdown_menu.find_elements(By.CSS_SELECTOR, TVSelectors.MENU_ITEMS)
            logger.debug(f"Found {len(menu_items)} options in dropdown")

            # Find the item containing indicator_name
            indicator_found = False
            for item in menu_items:
                try:
                    item_text = item.text
                    if indicator_name in item_text:
                        logger.info(f"Found indicator option: {item_text[:80]}...")
                        item.click()
                        indicator_found = True
                        time.sleep(0.5)
                        break
                except Exception:
                    continue

            if not indicator_found:
                logger.error(f"Indicator '{indicator_name}' not found in condition dropdown")
                self._close_alert_dialog(dialog)
                raise SeleniumError(f"Indicator '{indicator_name}' not found in condition dropdown")

            # Step 4: Click Notifications tab
            logger.info("Step 4: Switching to Notifications tab...")
            notifications_tab = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.NOTIFICATIONS_TAB))
            )
            notifications_tab.click()
            time.sleep(0.5)

            # Step 5: Enable webhook checkbox
            logger.info("Step 5: Enabling webhook...")
            webhook_checkbox = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, TVSelectors.WEBHOOK_CHECKBOX))
            )

            if not webhook_checkbox.is_selected():
                try:
                    webhook_checkbox.click()
                except Exception:
                    # Fallback to JavaScript click
                    driver.execute_script("arguments[0].click();", webhook_checkbox)
                logger.debug("Enabled webhook checkbox")
                time.sleep(0.3)
            else:
                logger.debug("Webhook checkbox already enabled")

            # Step 6: Enter webhook URL
            logger.info(f"Step 6: Entering webhook URL: {webhook_url}")
            webhook_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, TVSelectors.WEBHOOK_URL_INPUT))
            )
            # Click to focus, Ctrl+A to select all existing text, then type new URL
            webhook_input.click()
            webhook_input.send_keys(Keys.CONTROL + 'a')
            webhook_input.send_keys(Keys.DELETE)
            webhook_input.send_keys(webhook_url)
            time.sleep(0.5)

            # Step 7: Click Create button
            logger.info("Step 7: Clicking Create button...")
            create_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.SUBMIT_BUTTON))
            )
            create_btn.click()

            # Step 8: Wait for dialog to close (confirms success)
            logger.info("Step 8: Waiting for dialog to close...")
            try:
                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, TVSelectors.ALERT_DIALOG))
                )
            except TimeoutException:
                # Check if there's an error message
                try:
                    error = dialog.find_element(By.CSS_SELECTOR, TVSelectors.ALERT_ERROR_HINT)
                    if error.is_displayed():
                        error_text = error.text
                        logger.error(f"Alert creation failed: {error_text}")
                        self._close_alert_dialog(dialog)
                        raise SeleniumError(f"Alert creation failed: {error_text}")
                except NoSuchElementException:
                    pass  # No error element found, might still be processing

            logger.info(f"Successfully created webhook alert: {alert_name}")

            # Add 2 second wait at the end as required
            time.sleep(2)
            return True

        except TimeoutException as e:
            logger.error(f"Timeout during alert creation: {e}")
            try:
                dialog = driver.find_element(By.CSS_SELECTOR, TVSelectors.ALERT_DIALOG)
                self._close_alert_dialog(dialog)
            except Exception:
                pass
            raise SeleniumError(f"Alert creation timed out: {e}")
        except SeleniumError:
            raise
        except Exception as e:
            logger.error(f"Alert creation failed: {e}")
            try:
                dialog = driver.find_element(By.CSS_SELECTOR, TVSelectors.ALERT_DIALOG)
                self._close_alert_dialog(dialog)
            except Exception:
                pass
            raise SeleniumError(f"Alert creation failed: {e}")

    def _close_alert_dialog(self, dialog):
        """Close the alert dialog safely."""
        try:
            close_selectors = [
                TVSelectors.CLOSE_BUTTON,
                TVSelectors.CANCEL_BUTTON
            ]
            for selector in close_selectors:
                try:
                    btn = dialog.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed():
                        btn.click()
                        return
                except NoSuchElementException:
                    continue

            # Fallback: press Escape
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        except Exception as e:
            logger.warning(f"Could not close alert dialog: {e}")

    def process_nwe_batch(
        self,
        symbols: List[str],
        webhook_url: str,
        indicator_name: str = "TTE NWE Screener",
        timeframe: str = "4 hours"
    ) -> bool:
        """
        Process a batch of symbols through the NWE screener.

        High-level method that:
        1. Navigates to NWE chart
        2. Changes timeframe
        3. Deletes existing alerts
        4. Opens indicator settings
        5. Sets symbol inputs
        6. Clicks OK and waits for recalculation
        7. Creates webhook alert

        Args:
            symbols: List of symbols to scan (max 40)
            webhook_url: Webhook URL for alerts
            indicator_name: Name of NWE indicator in legend
            timeframe: Timeframe to use (default: "4 hours")

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing NWE batch with {len(symbols)} symbols")

        try:
            # Navigate to NWE chart
            if not config.NWE_CHART_URL:
                raise SeleniumError("NWE_CHART_URL not configured")
            self.navigate_to_chart(config.NWE_CHART_URL)

            # Change timeframe
            self.change_tframe(timeframe)

            # Pause existing alerts (safer than delete - no confirmation popup)
            self.pause_all_alerts()

            # Open indicator settings
            self.open_indicator_settings(indicator_name)

            # Set symbol inputs
            self.set_symbol_inputs(symbols, max_inputs=40)

            # Click OK and wait for recalculation
            self.click_ok_button(wait_for_recalc=True)

            # Create webhook alert
            self.create_webhook_alert(
                indicator_name=indicator_name,
                webhook_url=webhook_url,
                alert_name="TTE NWE Webhook"
            )

            logger.info(f"NWE batch processed successfully with {len(symbols)} symbols")
            return True

        except SeleniumError as e:
            logger.error(f"NWE batch processing failed: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error processing NWE batch")
            return False

    def process_obdiv_batch(
        self,
        symbols: List[str],
        webhook_url: str,
        indicator_name: str = "TTE OBDIV Screener",
        timeframe: str = "4 hours"
    ) -> bool:
        """
        Process a batch of symbols through the OBDIV screener.

        High-level method that:
        1. Navigates to OBDIV chart
        2. Changes timeframe
        3. Deletes existing alerts
        4. Opens indicator settings
        5. Sets symbol inputs
        6. Clicks OK and waits for recalculation
        7. Creates webhook alert

        Args:
            symbols: List of symbols to scan (max 10)
            webhook_url: Webhook URL for alerts
            indicator_name: Name of OBDIV indicator in legend
            timeframe: Timeframe to use (default: "4 hours")

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing OBDIV batch with {len(symbols)} symbols")

        try:
            # Navigate to OBDIV chart
            if not config.OBDIV_CHART_URL:
                raise SeleniumError("OBDIV_CHART_URL not configured")
            self.navigate_to_chart(config.OBDIV_CHART_URL)

            # Change timeframe
            self.change_tframe(timeframe)

            # Pause existing alerts (safer than delete - no confirmation popup)
            self.pause_all_alerts()

            # Open indicator settings
            self.open_indicator_settings(indicator_name)

            # Set symbol inputs
            self.set_symbol_inputs(symbols, max_inputs=10)

            # Click OK and wait for recalculation
            self.click_ok_button(wait_for_recalc=True)

            # Create webhook alert
            self.create_webhook_alert(
                indicator_name=indicator_name,
                webhook_url=webhook_url,
                alert_name="TTE OBDIV Webhook"
            )

            logger.info(f"OBDIV batch processed successfully with {len(symbols)} symbols")
            return True

        except SeleniumError as e:
            logger.error(f"OBDIV batch processing failed: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error processing OBDIV batch")
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
