"""
Selenium Browser Automation for TradingView.

Manages Chrome browser automation for:
- Updating symbol inputs in screener indicators
- Creating webhook alerts for TradingView indicators
- Capturing chart screenshots
- Navigating TradingView charts

Based on the working open_tv.py implementation.
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

from config import Config
from utils.logger import get_logger

logger = get_logger('selenium')


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
# These selectors are based on TradingView's current UI (as of 2026-01).
# If TradingView updates their UI, these may need to be updated.

class TVSelectors:
    """TradingView UI selectors organized by function."""

    # Legend / Indicator (FIXED: data-qa-id, not data-name - verified 2026-01-31)
    LEGEND_ITEM = 'div[data-qa-id="legend-source-item"]'
    INDICATOR_TITLE = 'div[class*="title"]'
    INDICATOR_SETTINGS_DIALOG = '[data-dialog-name="indicatorSettings"], .tv-dialog--indicator-properties'

    # Alert Dialog
    SET_ALERT_BUTTON = 'div[data-name="set-alert-button"]'
    ALERT_DIALOG = 'div[data-name="alerts-create-edit-dialog"]'
    ALERT_SOURCE_DROPDOWN = 'span[data-qa-id="ui-kit-disclosure-control main-series-select"]'
    ALERT_MENU_OPTIONS = 'div[data-name="menu-inner"] div[role="option"]'
    ALERT_NAME_INPUT = 'input[id="alert-name"]'
    ALERT_ERROR_HINT = 'div[data-name="error-hint"]'

    # Alert Notifications Tab (for webhook configuration)
    # NOTE: These selectors need to be verified via browser inspection.
    # The alert dialog has tabs: Condition, Actions, Notifications
    NOTIFICATIONS_TAB = 'button[id="notifications"], div[data-name="notifications-tab"], span:contains("Notifications")'
    WEBHOOK_URL_TOGGLE = 'input[name="webhook-url"], div[data-name="webhook-toggle"]'
    WEBHOOK_URL_INPUT = 'input[placeholder*="webhook"], input[data-name="webhook-url-input"]'
    ALERT_MESSAGE_INPUT = 'textarea[data-name="message-input"], textarea[class*="message"]'

    # Buttons
    SUBMIT_BUTTON = 'button[data-name="submit"]'
    APPLY_BUTTON = 'button[data-name="apply"]'
    CANCEL_BUTTON = 'button[data-name="cancel"]'
    CLOSE_BUTTON = 'button[data-name="close"]'
    OK_BUTTON_XPATH = "//button[contains(text(), 'OK')]"

    # Chart
    CHART_CONTAINER = '.chart-container'

    # Snapshot
    SNAPSHOT_URL_INPUT = "input[type='text'][readonly], .tv-snapshot-url input"


class SeleniumManager:
    """
    Manages browser automation for TradingView interactions.

    Handles:
    - Chrome driver lifecycle
    - TradingView chart navigation
    - Indicator settings modification
    - Screenshot capture

    Attributes:
        driver: Chrome WebDriver instance
        config: Configuration object
    """

    def __init__(self):
        """Initialize the Selenium manager."""
        self.driver: Optional[webdriver.Chrome] = None
        self.config = Config

    def get_driver(self) -> webdriver.Chrome:
        """
        Get or create Chrome driver instance.

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
        chrome_profiles_path = os.getenv("CHROME_PROFILES_PATH", 
            "C:/Users/dassa/AppData/Local/Google/Chrome/User Data")
        profile_name = os.getenv("CHROME_PROFILE_NAME", "Profile 3")
        
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
            self.driver.implicitly_wait(self.config.SELENIUM_IMPLICIT_WAIT)
            self.driver.set_page_load_timeout(self.config.PAGE_LOAD_TIMEOUT)
            
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

    def restart(self) -> webdriver.Chrome:
        """
        Restart the browser.

        Useful for clearing memory or recovering from errors.

        Returns:
            Fresh Chrome WebDriver instance
        """
        logger.info("Restarting Chrome driver...")
        self.close()
        time.sleep(2)  # Brief pause before restarting
        return self.get_driver()

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

    def navigate_to_chart(self, chart_url: str, wait_time: float = 5.0):
        """
        Navigate to a TradingView chart.

        Args:
            chart_url: Full URL to the chart
            wait_time: Seconds to wait for chart to load
        """
        driver = self.get_driver()
        logger.info(f"Navigating to: {chart_url}")

        try:
            driver.get(chart_url)
            time.sleep(wait_time)  # Wait for chart data to load

            # Check if we're logged in
            if self._check_login_required():
                logger.error("TradingView login required! Please log in manually.")
                raise SeleniumError(
                    "TradingView login required. Please open Chrome manually, "
                    "log into TradingView, then restart the orchestrator."
                )

            # Wait for chart container to be present
            WebDriverWait(driver, self.config.SELENIUM_EXPLICIT_WAIT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "chart-container"))
            )

            logger.debug("Chart loaded successfully")

        except TimeoutException:
            logger.warning("Chart container not found, continuing anyway")
        except WebDriverException as e:
            logger.error(f"Navigation failed: {e}")
            raise SeleniumError(f"Failed to navigate to chart: {e}")

    def open_indicator_settings(self, indicator_name: str):
        """
        Open settings dialog for an indicator.

        Args:
            indicator_name: Name of the indicator as shown in legend

        Raises:
            SeleniumError: If indicator not found or settings can't be opened
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, self.config.SELENIUM_EXPLICIT_WAIT)

        try:
            # Find indicator in legend area (FIXED: data-qa-id, not data-name)
            indicators = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div[data-qa-id="legend-source-item"]')
                )
            )
            
            indicator_element = None
            for ind in indicators:
                try:
                    title = ind.find_element(
                        By.CSS_SELECTOR, 'div[class*="title"]'
                    ).text
                    if indicator_name in title:
                        indicator_element = ind
                        break
                except:
                    continue
            
            if not indicator_element:
                raise SeleniumError(f"Indicator not found: {indicator_name}")

            # Double-click to open settings
            actions = ActionChains(driver)
            actions.double_click(indicator_element).perform()

            # Wait for settings dialog to appear
            wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "[data-dialog-name='indicatorSettings'], .tv-dialog--indicator-properties"
                ))
            )

            logger.info(f"Opened settings for: {indicator_name}")
            time.sleep(1)  # Brief pause for dialog animation

        except TimeoutException:
            logger.error(f"Could not find or open settings for: {indicator_name}")
            raise SeleniumError(f"Indicator not found: {indicator_name}")

    def set_symbol_inputs(self, symbols: List[str], max_inputs: int = 20):
        """
        Set symbol input fields in indicator settings dialog.

        Args:
            symbols: List of symbols to set
            max_inputs: Maximum number of input fields
        """
        driver = self.get_driver()

        try:
            # Find all symbol input fields in the settings dialog
            dialog_selector = "[data-dialog-name='indicatorSettings'], .tv-dialog--indicator-properties"
            dialog = driver.find_element(By.CSS_SELECTOR, dialog_selector)

            # Find symbol inputs
            inputs = dialog.find_elements(
                By.CSS_SELECTOR,
                "input[type='text'], input.tv-symbol-input"
            )

            # Filter to get only symbol-related inputs
            symbol_inputs = []
            for inp in inputs:
                try:
                    placeholder = inp.get_attribute('placeholder') or ''
                    data_name = inp.get_attribute('data-name') or ''
                    value = inp.get_attribute('value') or ''

                    if ':' in value or 'symbol' in placeholder.lower() or 'symbol' in data_name.lower():
                        symbol_inputs.append(inp)
                except StaleElementReferenceException:
                    continue

            logger.debug(f"Found {len(symbol_inputs)} symbol inputs")

            # Set symbol values
            for i, inp in enumerate(symbol_inputs[:max_inputs]):
                symbol = symbols[i] if i < len(symbols) else ""

                try:
                    inp.clear()
                    if symbol:
                        inp.send_keys(symbol)
                    logger.debug(f"Set input {i + 1} to: {symbol or '(empty)'}")
                except StaleElementReferenceException:
                    logger.warning(f"Input {i + 1} became stale, skipping")
                    continue

            logger.info(f"Set {min(len(symbols), len(symbol_inputs))} symbol inputs")

        except NoSuchElementException as e:
            logger.error(f"Could not find symbol inputs: {e}")
            raise SeleniumError("Symbol inputs not found in settings dialog")

    def click_ok_button(self):
        """
        Click OK/Apply button to save indicator settings.

        Raises:
            SeleniumError: If button not found
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, self.config.SELENIUM_EXPLICIT_WAIT)

        try:
            button_selectors = [
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
                time.sleep(2)
            else:
                raise SeleniumError("OK/Apply button not found")

        except TimeoutException:
            logger.error("Could not find OK/Apply button")
            raise SeleniumError("OK/Apply button not found")

    def update_nwe_symbols(self, symbols: List[str]):
        """
        Update symbol inputs in the NWE screener indicator.

        Args:
            symbols: List of symbols to set (max 20)
        """
        logger.info(f"Updating NWE screener with {len(symbols)} symbols")

        if not self.config.NWE_CHART_URL:
            raise SeleniumError("NWE_CHART_URL not configured")

        self.navigate_to_chart(self.config.NWE_CHART_URL)
        self.open_indicator_settings("TTE NWE Screener")
        self.set_symbol_inputs(symbols, max_inputs=20)
        self.click_ok_button()

        # Delete existing alerts and create new webhook alert
        self.delete_all_alerts()
        self.create_webhook_alert("TTE NWE Screener", self.config.NWE_WEBHOOK_URL, "NWE Alert")

        logger.info("NWE screener symbols updated and alert created")

    def update_obdiv_symbols(self, symbols: List[str]):
        """
        Update symbol inputs in the OBDIV screener indicator.

        Args:
            symbols: List of symbols to set (max 8)
        """
        logger.info(f"Updating OBDIV screener with {len(symbols)} symbols")

        if not self.config.OBDIV_CHART_URL:
            raise SeleniumError("OBDIV_CHART_URL not configured")

        self.navigate_to_chart(self.config.OBDIV_CHART_URL)
        self.open_indicator_settings("TTE OBDIV Screener")
        self.set_symbol_inputs(symbols[:8], max_inputs=8)
        self.click_ok_button()

        # Delete existing alerts and create new webhook alert
        self.delete_all_alerts()
        self.create_webhook_alert("TTE OBDIV Screener", self.config.OBDIV_WEBHOOK_URL, "OBDIV Alert")

        logger.info("OBDIV screener symbols updated and alert created")

    def set_symbol_inputs_by_label(self, symbols: List[str], label_prefix: str = "Symbol"):
        """
        Set symbol input fields using label-based matching (more reliable).

        This method finds inputs by matching their labels, which is more reliable
        than the heuristic approach in set_symbol_inputs().

        Args:
            symbols: List of symbols to set
            label_prefix: Label prefix to match (e.g., "Symbol" for Symbol1, Symbol2, etc.)

        Returns:
            Number of symbols successfully set
        """
        driver = self.get_driver()

        try:
            # Find the settings dialog
            dialog = driver.find_element(
                By.CSS_SELECTOR, TVSelectors.INDICATOR_SETTINGS_DIALOG
            )

            # Find all input rows/groups
            # Try multiple selectors for different dialog layouts
            row_selectors = [
                '.inputRow',
                '[class*="inputRow"]',
                '.property-row',
                '[class*="property"]',
                '.cell-input'
            ]

            rows = []
            for selector in row_selectors:
                found = dialog.find_elements(By.CSS_SELECTOR, selector)
                if found:
                    rows = found
                    break

            if not rows:
                logger.warning("No input rows found, falling back to heuristic method")
                return self.set_symbol_inputs(symbols, max_inputs=len(symbols))

            symbol_index = 0
            for row in rows:
                try:
                    # Try to find label in this row
                    label_selectors = ['.label', '[class*="label"]', 'span', 'div']
                    label_text = ""

                    for sel in label_selectors:
                        try:
                            label_elem = row.find_element(By.CSS_SELECTOR, sel)
                            label_text = label_elem.text.strip()
                            if label_text:
                                break
                        except NoSuchElementException:
                            continue

                    # Check if this label matches our pattern (e.g., "Symbol1", "Symbol2")
                    if label_text.startswith(label_prefix):
                        # Extract the number suffix if present
                        suffix = label_text[len(label_prefix):]
                        if suffix.isdigit() or suffix == "":
                            # Found a symbol input row
                            input_field = row.find_element(By.CSS_SELECTOR, 'input')
                            if symbol_index < len(symbols):
                                input_field.clear()
                                input_field.send_keys(symbols[symbol_index])
                                logger.debug(f"Set {label_text} to: {symbols[symbol_index]}")
                                symbol_index += 1

                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            logger.info(f"Set {symbol_index} symbol inputs using label matching")
            return symbol_index

        except NoSuchElementException as e:
            logger.error(f"Could not find dialog or inputs: {e}")
            raise SeleniumError("Settings dialog not found for label-based input")

    @retry_on_failure(max_retries=2, delay=1.0)
    def create_webhook_alert(
        self,
        indicator_name: str,
        webhook_url: str,
        alert_name: str = "",
        message_template: str = "{{alert.message}}"
    ) -> bool:
        """
        Create a TradingView alert with webhook configuration.

        This method creates an alert for the specified indicator and configures
        it to send webhooks to the given URL.

        Args:
            indicator_name: Short title of the indicator (as shown in legend)
            webhook_url: URL to send webhook POST requests to
            alert_name: Name for the alert (optional, uses default if empty)
            message_template: Message format template (default: {{alert.message}})

        Returns:
            True if alert was created successfully

        Raises:
            SeleniumError: If alert creation fails

        Note:
            The Notifications tab selectors may need to be updated if TradingView
            changes their UI. Run test_browser_quick.py to verify selectors.
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, self.config.SELENIUM_EXPLICIT_WAIT)

        try:
            # Step 1: Click "+" button to open alert dialog
            logger.info(f"Creating webhook alert for: {indicator_name}")
            plus_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.SET_ALERT_BUTTON))
            )
            plus_button.click()

            # Step 2: Wait for alert dialog
            dialog = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, TVSelectors.ALERT_DIALOG))
            )
            time.sleep(1)  # Brief pause for dialog animation

            # Step 3: Select indicator as source
            source_dropdown = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, TVSelectors.ALERT_SOURCE_DROPDOWN))
            )
            source_dropdown.click()

            # Find and select the indicator
            indicator_found = False
            options = driver.find_elements(By.CSS_SELECTOR, TVSelectors.ALERT_MENU_OPTIONS)
            for opt in options:
                if indicator_name in opt.text:
                    opt.click()
                    indicator_found = True
                    logger.debug(f"Selected indicator: {indicator_name}")
                    break

            if not indicator_found:
                logger.error(f"Indicator not found in dropdown: {indicator_name}")
                self._close_alert_dialog(dialog)
                raise SeleniumError(f"Indicator '{indicator_name}' not found in alert source dropdown")

            time.sleep(0.5)

            # Step 4: Navigate to Notifications tab
            # TradingView alert dialog has tabs. We need to click "Notifications" tab.
            # NOTE: These selectors need verification via browser inspection.
            notifications_tab_selectors = [
                'button[id="notifications"]',
                'div[data-name="notifications-tab"]',
                '//span[contains(text(), "Notifications")]',
                '//div[contains(@class, "tab")][contains(text(), "Notifications")]',
                '[data-dialog-name="alerts-create-edit-dialog"] button:nth-child(3)'  # Usually 3rd tab
            ]

            tab_clicked = False
            for selector in notifications_tab_selectors:
                try:
                    if selector.startswith('//'):
                        tab = driver.find_element(By.XPATH, selector)
                    else:
                        tab = driver.find_element(By.CSS_SELECTOR, selector)
                    if tab.is_displayed():
                        tab.click()
                        tab_clicked = True
                        logger.debug("Clicked Notifications tab")
                        break
                except NoSuchElementException:
                    continue

            if not tab_clicked:
                logger.warning(
                    "Could not find Notifications tab. "
                    "Webhook may need to be configured manually. "
                    "Please run browser inspection to update selectors."
                )
                # Continue anyway - alert creation will still work, just without webhook

            time.sleep(0.5)

            # Step 5: Enable and configure webhook
            # NOTE: These selectors need verification via browser inspection.
            webhook_configured = False

            # Try to find webhook toggle/checkbox
            webhook_toggle_selectors = [
                'input[name="webhook-url"]',
                'div[data-name="webhook-toggle"]',
                'input[type="checkbox"][id*="webhook"]',
                '//input[@type="checkbox"]//following-sibling::span[contains(text(), "Webhook")]/../input',
                'label:contains("Webhook URL") input'
            ]

            for selector in webhook_toggle_selectors:
                try:
                    if selector.startswith('//'):
                        toggle = driver.find_element(By.XPATH, selector)
                    else:
                        toggle = driver.find_element(By.CSS_SELECTOR, selector)

                    # If it's a checkbox and not checked, click it
                    if toggle.tag_name == 'input' and toggle.get_attribute('type') == 'checkbox':
                        if not toggle.is_selected():
                            toggle.click()
                            logger.debug("Enabled webhook checkbox")
                    break
                except NoSuchElementException:
                    continue

            # Try to find and fill webhook URL input
            webhook_url_selectors = [
                'input[placeholder*="webhook"]',
                'input[data-name="webhook-url-input"]',
                'input[placeholder*="URL"]',
                'input[type="text"][class*="webhook"]',
                '//input[@placeholder and contains(@placeholder, "https://")]'
            ]

            for selector in webhook_url_selectors:
                try:
                    if selector.startswith('//'):
                        url_input = driver.find_element(By.XPATH, selector)
                    else:
                        url_input = driver.find_element(By.CSS_SELECTOR, selector)

                    if url_input.is_displayed():
                        url_input.clear()
                        url_input.send_keys(webhook_url)
                        webhook_configured = True
                        logger.info(f"Configured webhook URL: {webhook_url}")
                        break
                except NoSuchElementException:
                    continue

            if not webhook_configured:
                logger.warning(
                    "Could not configure webhook URL. "
                    "Selectors may need updating. "
                    "Alert will be created without webhook - configure manually."
                )

            # Step 6: Set message template
            message_configured = False
            message_selectors = [
                'textarea[data-name="message-input"]',
                'textarea[class*="message"]',
                'textarea[placeholder*="message"]',
                '//textarea'
            ]

            for selector in message_selectors:
                try:
                    if selector.startswith('//'):
                        msg_input = driver.find_element(By.XPATH, selector)
                    else:
                        msg_input = driver.find_element(By.CSS_SELECTOR, selector)

                    if msg_input.is_displayed():
                        msg_input.clear()
                        msg_input.send_keys(message_template)
                        message_configured = True
                        logger.debug(f"Set message template: {message_template}")
                        break
                except NoSuchElementException:
                    continue

            # Step 7: Set alert name (if provided)
            if alert_name:
                try:
                    name_input = dialog.find_element(By.CSS_SELECTOR, TVSelectors.ALERT_NAME_INPUT)
                    name_input.send_keys(Keys.CONTROL + "a")
                    name_input.send_keys(Keys.BACKSPACE)
                    name_input.send_keys(alert_name)
                    logger.debug(f"Set alert name: {alert_name}")
                except NoSuchElementException:
                    logger.warning("Could not find alert name input")

            # Step 8: Submit alert
            submit_button = dialog.find_element(By.CSS_SELECTOR, TVSelectors.SUBMIT_BUTTON)
            submit_button.click()
            logger.info("Clicked Create button")

            # Step 9: Check for errors
            time.sleep(2)
            try:
                error = dialog.find_element(By.CSS_SELECTOR, TVSelectors.ALERT_ERROR_HINT)
                if error.is_displayed():
                    error_text = error.text
                    logger.error(f"Alert creation failed: {error_text}")
                    self._close_alert_dialog(dialog)
                    raise SeleniumError(f"Alert creation failed: {error_text}")
            except NoSuchElementException:
                pass  # No error - success!

            logger.info(f"Alert created successfully for: {indicator_name}")
            return True

        except TimeoutException as e:
            logger.error(f"Timeout during alert creation: {e}")
            raise SeleniumError(f"Alert creation timed out: {e}")
        except Exception as e:
            logger.error(f"Alert creation failed: {e}")
            # Try to close dialog if it's open
            try:
                dialog = driver.find_element(By.CSS_SELECTOR, TVSelectors.ALERT_DIALOG)
                self._close_alert_dialog(dialog)
            except:
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

    def delete_all_alerts(self):
        """
        Delete all alerts in TradingView.

        Ported from open_tv.py for completeness.

        Returns:
            True if successful
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, self.config.SELENIUM_EXPLICIT_WAIT)

        try:
            # Open alerts settings menu
            settings_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))
            )
            settings_btn.click()

            # Click "Delete all alerts" option
            menu = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]'))
            )

            delete_option = None
            for item in menu.find_elements(By.CSS_SELECTOR, 'div[role="menuitem"]'):
                if 'delete' in item.text.lower() and 'all' in item.text.lower():
                    delete_option = item
                    break

            if delete_option:
                delete_option.click()

                # Confirm deletion
                time.sleep(1)
                confirm_selectors = [
                    'button[data-name="confirm-yes"]',
                    '//button[contains(text(), "Yes")]',
                    '//button[contains(text(), "Delete")]'
                ]
                for selector in confirm_selectors:
                    try:
                        if selector.startswith('//'):
                            confirm = driver.find_element(By.XPATH, selector)
                        else:
                            confirm = driver.find_element(By.CSS_SELECTOR, selector)
                        confirm.click()
                        logger.info("All alerts deleted")
                        return True
                    except NoSuchElementException:
                        continue

            logger.warning("Could not find 'Delete all alerts' option")
            return False

        except TimeoutException:
            logger.warning("Could not find alerts settings button")
            return False
        except Exception as e:
            logger.error(f"Failed to delete alerts: {e}")
            return False

    def verify_indicator_loaded(self, indicator_name: str, timeout: int = 30) -> bool:
        """
        Verify that an indicator is loaded and visible on the chart.

        Args:
            indicator_name: Name of the indicator to check
            timeout: Maximum time to wait in seconds

        Returns:
            True if indicator is found and loaded
        """
        driver = self.get_driver()

        try:
            wait = WebDriverWait(driver, timeout)
            indicators = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, TVSelectors.LEGEND_ITEM)
                )
            )

            for ind in indicators:
                try:
                    title = ind.find_element(
                        By.CSS_SELECTOR, TVSelectors.INDICATOR_TITLE
                    ).text
                    if indicator_name in title:
                        # Check for error state
                        try:
                            error = ind.find_element(By.CSS_SELECTOR, '[class*="error"]')
                            if error.is_displayed():
                                logger.warning(f"Indicator has error: {indicator_name}")
                                return False
                        except NoSuchElementException:
                            pass  # No error - good

                        logger.debug(f"Indicator verified: {indicator_name}")
                        return True
                except:
                    continue

            logger.warning(f"Indicator not found: {indicator_name}")
            return False

        except TimeoutException:
            logger.warning(f"Timeout waiting for indicator: {indicator_name}")
            return False

    def capture_chart_screenshot(self, symbol: str, timeframe: str) -> str:
        """
        Navigate to symbol chart and capture screenshot.

        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Chart timeframe (e.g., "240" for H4, "D" for daily)

        Returns:
            Screenshot URL or local file path
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, self.config.SELENIUM_EXPLICIT_WAIT)

        chart_url = f"https://www.tradingview.com/chart/?symbol={symbol}&interval={timeframe}"
        self.navigate_to_chart(chart_url, wait_time=self.config.SCREENSHOT_WAIT)

        try:
            # Try TradingView's native snapshot (Alt+S)
            actions = ActionChains(driver)
            actions.key_down(Keys.ALT).send_keys('s').key_up(Keys.ALT).perform()
            time.sleep(2)

            snapshot_input = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "input[type='text'][readonly], .tv-snapshot-url input"
                ))
            )

            screenshot_url = snapshot_input.get_attribute('value')

            try:
                close_btn = driver.find_element(
                    By.CSS_SELECTOR,
                    "button[data-name='close'], .tv-dialog__close"
                )
                close_btn.click()
            except NoSuchElementException:
                actions.send_keys(Keys.ESCAPE).perform()

            logger.info(f"Screenshot captured: {screenshot_url}")
            return screenshot_url

        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"TradingView snapshot failed: {e}. Using fallback.")

            screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)

            filename = f"{symbol}_{timeframe}_{int(time.time())}.png"
            filepath = os.path.join(screenshots_dir, filename)

            driver.save_screenshot(filepath)
            logger.info(f"Fallback screenshot saved: {filepath}")

            return filepath

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
