"""
Browser automation for TradingView. Handles sign-in, layout/timeframe management,
screener indicator configuration, webhook alert creation, and indicator re-uploading.
"""

import platform
import subprocess
from os import getenv
from pathlib import Path
from time import sleep, time

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tte import log
from tte.browser.chart import OpenChart
from tte.browser.helpers import Utils
from tte.config import PROFILE

# Set up logger for this file
open_tv_logger = log.setup_logger(__name__, log.INFO)

# some constants
LAYOUT_NAME = "Screener"  # Name of the layout for the screener
CHART_TIMEFRAME = "1 hour"  # default chart timeframe
SCREENER_REUPLOAD_TIMEOUT = (
    15  # seconds to wait for the screener to show up on the chart after re-uploading it
)

CHROME_PROFILES_PATH = getenv("CHROME_PROFILES_PATH")


def _get_chrome_major_version() -> str | None:
    """Get the major version of the installed Chrome browser (e.g. '145')."""
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"&{{(Get-Item '{chrome_path}').VersionInfo.ProductVersion}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = result.stdout.strip()
        if version and "." in version:
            return version.split(".")[0]
    except Exception as e:
        open_tv_logger.debug(f"Could not detect Chrome version: {e}")
    return None


def _find_chromedriver() -> str | None:
    """Find a cached chromedriver, matching Chrome's major version if possible.

    Fallback chain:
    1. CHROMEDRIVER_PATH env var (explicit override)
    2. ~/.wdm/drivers/chromedriver/win64/ cache (version-matched)
    3. None (let Selenium auto-discover via SeleniumManager)
    """
    # 1. Explicit env var override
    env_path = getenv("CHROMEDRIVER_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            open_tv_logger.debug(f"Using CHROMEDRIVER_PATH env var: {p}")
            return str(p)
        open_tv_logger.warning(f"CHROMEDRIVER_PATH set but not found: {env_path}")

    # 2. Scan webdriver-manager cache
    wdm_cache = Path.home() / ".wdm" / "drivers" / "chromedriver" / "win64"
    if not wdm_cache.is_dir():
        return None

    chrome_major = _get_chrome_major_version()
    best_match = None

    for version_dir in sorted(wdm_cache.iterdir(), reverse=True):
        if not version_dir.is_dir():
            continue
        # Look for chromedriver.exe in any subdirectory
        candidates = list(version_dir.rglob("chromedriver.exe"))
        if not candidates:
            continue
        candidate = candidates[0]
        # If we know Chrome's major version, prefer a matching driver
        if chrome_major and version_dir.name.startswith(chrome_major + "."):
            open_tv_logger.debug(f"Found version-matched chromedriver: {candidate}")
            return str(candidate)
        # Otherwise keep the newest as fallback
        if best_match is None:
            best_match = candidate

    if best_match:
        open_tv_logger.debug(f"Using best-available cached chromedriver: {best_match}")
        return str(best_match)

    return None


# class
class Browser:
    def __init__(
        self,
        keep_open: bool,
        screener_shorttitle: str,
        screener_name: str,
        drawer_shorttitle: str,
        drawer_name: str,
        interval_minutes: int,
        start_fresh: bool,
        screener_ob_short: str,
        screener_ob_name: str,
        screener_nw_short: str,
        screener_nw_name: str,
        screener_sb_short: str,
        screener_sb_name: str,
        mode: str = "legacy",
        layout_name: str | None = None,
        chart_timeframe: str | None = None,
        bar_style: str | None = None,
        chrome_profile: str | None = None,
        user_data_suffix: str = "",
        browser_id: int = 0,
        headless: bool = False,
    ) -> None:
        open_tv_logger.debug("Browser.__init__() called")

        # Use provided chrome_profile or fall back to env var PROFILE
        actual_profile = chrome_profile or PROFILE
        open_tv_logger.debug(f"Chrome profile: {actual_profile}")

        # Kill Chrome processes that would conflict with our user-data-dir.
        # Linux/Docker containers start with a fresh user-data-dir on every run, so
        # there's never a leftover Chrome to kill — and `powershell` / `taskkill`
        # don't exist there. Skip entirely outside Windows.
        if browser_id == 0 and platform.system() == "Windows":
            # Combo mode (first browser only): kill Chrome processes using TTE user-data-dirs
            # This prevents profile lock conflicts without killing unrelated Chrome windows
            open_tv_logger.debug("Killing Chrome processes using TTE profiles...")
            try:
                ps_cmd = (
                    "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
                    "Where-Object { $_.CommandLine -match 'TTE' } | "
                    "Select-Object -ExpandProperty ProcessId"
                )
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                pids = [p.strip() for p in result.stdout.strip().split("\n") if p.strip().isdigit()]
                if pids:
                    for pid in pids:
                        subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            capture_output=True,
                            timeout=5,
                        )
                    open_tv_logger.debug(f"Killed {len(pids)} Chrome processes using TTE profiles")
                    sleep(2)
                else:
                    open_tv_logger.debug("No existing TTE Chrome processes found")
            except Exception as e:
                open_tv_logger.debug(f"Could not check/kill TTE Chrome processes: {e}")

        chrome_options = Options()
        chrome_options.add_experimental_option("detach", keep_open)

        # Apply user data suffix for parallel browsers
        user_data_dir = f"{CHROME_PROFILES_PATH}/TTE{user_data_suffix}"
        open_tv_logger.debug(f"Chrome user data dir: {user_data_dir}")
        chrome_options.add_argument(f"--profile-directory={actual_profile}")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        # Removed --remote-debugging-port=9224 as it can cause conflicts
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")  # Helps with crashes
        chrome_options.add_argument("--disable-software-rasterizer")  # Helps with crashes

        # Prevent Chrome from throttling backgrounded/occluded windows (critical for parallel browsers)
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")

        # Headless mode (Chrome 109+ new headless)
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
            open_tv_logger.debug("Running in headless mode")

        # Add unique remote debugging port per browser_id to avoid conflicts
        if chrome_profile is not None:
            debug_port = 9222 + browser_id
            chrome_options.add_argument(f"--remote-debugging-port={debug_port}")
            open_tv_logger.debug(f"Remote debugging port: {debug_port} (browser_id={browser_id})")

        open_tv_logger.debug("Creating Chrome webdriver...")
        # Use unique ChromeDriver service port per browser to avoid collisions
        # port=0 means auto-assign (preserves legacy behavior when no chrome_profile)
        service_port = 9515 + browser_id if chrome_profile is not None else 0
        if service_port:
            open_tv_logger.debug(
                f"ChromeDriver service port: {service_port} (browser_id={browser_id})"
            )
        chromedriver_path = _find_chromedriver()
        if chromedriver_path:
            open_tv_logger.info(f"Using cached chromedriver: {chromedriver_path}")
            service = ChromeService(executable_path=chromedriver_path, port=service_port)
        else:
            open_tv_logger.info("No cached chromedriver found, using Selenium auto-discovery")
            service = ChromeService(port=service_port)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        open_tv_logger.debug("Chrome webdriver created successfully")

        self.open_chart = OpenChart(self.driver)
        self.utils = Utils()
        self.screener_name = screener_name
        self.screener_shorttitle = screener_shorttitle
        self.drawer_name = drawer_name
        self.drawer_shorttitle = drawer_shorttitle
        self.screener_ob_short = screener_ob_short
        self.screener_ob_name = screener_ob_name
        self.screener_nw_short = screener_nw_short
        self.screener_nw_name = screener_nw_name
        self.screener_sb_short = screener_sb_short
        self.screener_sb_name = screener_sb_name
        self.interval_seconds = interval_minutes * 60  # Convert the interval to seconds
        self.start_fresh = start_fresh
        self.mode = mode
        self.layout_name = layout_name or LAYOUT_NAME
        self.chart_timeframe = chart_timeframe or CHART_TIMEFRAME
        self.bar_style = bar_style or "line"  # Legacy default
        self.headless = headless
        self.init_succeeded = True
        self.tv_email = ""
        self.tv_password = ""

    def open_page(self, url: str):
        """This opens `url` and maximizes the window"""
        try:
            self.driver.get(url)
            if not getattr(self, "headless", False):
                self.driver.maximize_window()
            return True
        except WebDriverException:
            open_tv_logger.exception(f"Cannot open this url: {url}. Error: ")
            return False

    def sign_in(self):
        """This signs in to TradingView if logged out"""
        self.driver.get("https://www.tradingview.com/accounts/signin/")
        if not getattr(self, "headless", False):
            try:
                self.driver.maximize_window()
            except Exception:
                pass  # Already maximized or state transition failed
        try:
            # If the products menu is found, the user is signed in
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'a[data-main-menu-root-track-id="products"]')
                )
            )
            return True
        except TimeoutException:  # If the products menu is not found, the user is not signed in
            open_tv_logger.warning(
                "Products menu not found within 5 seconds. User might not be signed in."
            )
            # Attempt automated email/password login
            # This may fail if TradingView shows 2FA, CAPTCHA, or different page state
            try:
                tv_email = getenv("TRADINGVIEW_EMAIL")
                tv_password = getenv("TRADINGVIEW_PASSWORD")

                if not tv_email or not tv_password:
                    open_tv_logger.warning(
                        "TradingView credentials not found in environment variables. Waiting for manual sign-in..."
                    )
                    raise Exception("No credentials")

                # wait for the name="Email" button to be present and click it
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "Email"))
                ).click()

                # Wait for the email input field to be present
                email_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "id_username"))
                )
                email_input.send_keys(tv_email)

                # Wait for the password input field to be present
                password_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "id_password"))
                )
                password_input.send_keys(tv_password)

                # Wait for the sign in button to be clickable
                sign_in_button = self.driver.find_element(
                    By.CSS_SELECTOR, 'button[data-overflow-tooltip-text="Sign in"]'
                )
                sign_in_button.click()
            except Exception as e:
                open_tv_logger.warning(
                    f"Automated login failed ({e}). Waiting for manual sign-in..."
                )

            # Always wait up to 60s for sign-in to complete (handles 2FA, manual login, etc.)
            try:
                open_tv_logger.info("Waiting up to 60s for sign-in (enter 2FA code if prompted)...")
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'a[data-main-menu-root-track-id="products"]')
                    )
                )
                open_tv_logger.info("Successfully signed in to TradingView")
                return True
            except TimeoutException:
                open_tv_logger.error("Failed to sign in to TradingView (timed out after 60s)")
                return False

    def setup_tv(self):
        """Opens TradingView, changes the layout, sets the timeframe, opens the alert sidebar,
        verifies the screener indicator is on the chart, and makes it visible."""

        # sign in to tradingview
        if not self.sign_in():
            open_tv_logger.error("Failed to sign in to TradingView. Exiting function")
            return False

        # open tradingview
        if not self.open_page("https://www.tradingview.com/chart"):
            if not self.open_page("https://www.tradingview.com/chart"):  # try once more
                open_tv_logger.error("Failed to open tradingview. Exiting function")
                return False

        # change to the correct layout (if we are on any other layout)
        if not self.change_layout(self.layout_name):
            self.change_layout(self.layout_name)  # try once more
            if self.current_layout() != self.layout_name:
                open_tv_logger.error(
                    f"Cannot change the layout to {self.layout_name}. Exiting function"
                )
                return False

        # set the timeframe to the correct timeframe
        if not self.open_chart.change_tframe(self.chart_timeframe):
            self.open_chart.change_tframe(self.chart_timeframe)  # try once more
            if self.current_chart_tframe() != self.chart_timeframe:
                open_tv_logger.error(
                    f"Cannot change the chart timeframe to {self.chart_timeframe}. Exiting function"
                )
                return False

        # open the alerts sidebar
        if not self.open_alerts_sidebar():
            self.open_alerts_sidebar()  # try once more
            if not self.is_alerts_sidebar_open():
                open_tv_logger.error("Cannot open the alerts sidebar. Exiting function")
                return False

        # delete all alerts
        if self.start_fresh:
            if not self.delete_all_alerts():
                self.delete_all_alerts()  # try once more
                if not self.no_alerts():
                    open_tv_logger.error("Cannot delete all alerts. Exiting function")
                    return False
            open_tv_logger.info("All existing alerts deleted successfully")

        # Verify screener is on the chart (warning only — maintenance + snapshots work without it)
        screener_check = self.get_indicator(self.screener_ob_short)
        if screener_check is None:
            screener_check = self.get_indicator(self.screener_ob_short)
        if screener_check is None:
            open_tv_logger.warning(
                f"Screener '{self.screener_ob_short}' not found on chart — continuing anyway"
            )

        # Make the screener visible
        if not self.indicator_visibility(True, self.screener_ob_short):
            self.indicator_visibility(True, self.screener_ob_short)
            if not self.is_visible(self.screener_ob_short):
                open_tv_logger.warning(
                    f"Failed to make screener '{self.screener_ob_short}' visible. Continuing anyway."
                )

        # Change the bar style
        candle_type = self.bar_style
        if not self.change_candles_type(candle_type):
            open_tv_logger.warning(
                f"Failed to change the candle type to {candle_type}. Application will still continue on without exiting as this is not crucial."
            )

        # save the layout
        if not self.save_layout():
            if not self.save_layout():  # try once more
                open_tv_logger.warning(
                    f"Cannot save the current layout {self.layout_name}. The function will still continue on without exiting as this is not crucial."
                )

        # Dismiss any lingering dialogs/overlays (prevents click interception)
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            sleep(0.5)
        except Exception:
            pass  # Not critical if no dialog was open

        # give it some time to rest
        sleep(2)

        return True

    def change_layout(self, layout_name):
        """This changes the layout of the chart to `layout_name` if we are a different one. If we are on the same layout, it does nothing."""
        try:
            if self.current_layout() == layout_name:
                return True

            # Click the dropdown arrow (Manage layouts button)
            dropdown_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-name="save-load-menu"]'))
            )
            ActionChains(self.driver).click(dropdown_btn).perform()

            # Wait for dropdown menu to render
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'))
            )
            sleep(0.3)

            # Find layout in "Recently used" section by visible text
            # Scoped to data-qa-id to avoid matching chart legend or other page elements
            layout_item = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@data-qa-id="save-load-menu-item-recent"]'
                        f'[.//span[normalize-space(text())="{layout_name}"]]',
                    )
                )
            )

            # Non-current layouts are <a target="_blank"> links.
            # Clicking them opens a new tab — navigate directly instead.
            href = layout_item.get_attribute("href")
            if href:
                full_url = href if href.startswith("http") else f"https://www.tradingview.com{href}"
                self.driver.get(full_url)
                # Wait for the new layout page to fully load
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "button#header-toolbar-save-load")
                    )
                )
                sleep(2)
            else:
                # Current layout item is a <div>, not a link — just click it
                ActionChains(self.driver).click(layout_item).perform()
                sleep(0.5)
            return True
        except Exception:
            open_tv_logger.exception("An error happened when changing the layout. Error: ")
            return False

    def current_layout(self):
        """This returns the current layout of the chart."""
        try:
            curr_layout = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button#header-toolbar-save-load"))
            )
            return curr_layout.text.strip()
        except Exception:
            open_tv_logger.exception("An error happened when getting the current layout. Error: ")
            return ""

    def save_layout(self):
        """This saves the current layout of the chart by clicking on the current layout."""
        try:
            curr_layout = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]'))
            )
            curr_layout.click()
            sleep(0.5)
            open_tv_logger.info("Saved the current layout!")
            return True

        except Exception:
            open_tv_logger.exception("An error happened when saving the layout. Error: ")
            return False

    def _close_dropdown_by_clicking_settings(self):
        """Helper method to close any open dropdown by clicking on the settings modal.
        This prevents UI issues where an open dropdown blocks further interactions."""
        try:
            settings = self.driver.find_element(By.CSS_SELECTOR, ".content-tBgV1m0B")
            settings.click()
            sleep(0.5)
        except Exception:
            pass

    def change_settings(self, symbols_list, screener_shorttitle=None):
        """This changes the settings of a screener. It fills in the symbols and clicks on Submit.

        Args:
            symbols_list: List of symbols to input into the screener
            screener_shorttitle: The short title of the screener to configure. If None, uses all 3 screeners.
        """
        try:
            # Keep full symbol with exchange prefix (e.g., "NSE:RELIANCE") for unambiguous resolution.
            # TradingView's input.symbol() search accepts "EXCHANGE:SYMBOL" format.
            # Stripping the prefix causes ambiguous resolution for stocks listed on multiple exchanges.
            open_tv_logger.info(f"Setting symbols (with exchange prefix): {symbols_list[:5]}...")
            # Determine which screeners to configure
            screeners_to_configure = []
            if screener_shorttitle:
                # Configure specific screener - get fresh indicator reference
                if screener_shorttitle == self.screener_ob_short:
                    indicator = self._safe_indicator_access(self.screener_ob_short)
                    screeners_to_configure = [(self.screener_ob_short, indicator)]
                elif screener_shorttitle == self.screener_nw_short:
                    indicator = self._safe_indicator_access(self.screener_nw_short)
                    screeners_to_configure = [(self.screener_nw_short, indicator)]
                elif screener_shorttitle == self.screener_sb_short:
                    indicator = self._safe_indicator_access(self.screener_sb_short)
                    screeners_to_configure = [(self.screener_sb_short, indicator)]
                else:
                    open_tv_logger.error(f"Unknown screener shorttitle: {screener_shorttitle}")
                    return False
            else:
                # Configure all 3 screeners - get fresh indicator references
                screeners_to_configure = [
                    (
                        self.screener_ob_short,
                        self._safe_indicator_access(self.screener_ob_short),
                    ),
                    (
                        self.screener_nw_short,
                        self._safe_indicator_access(self.screener_nw_short),
                    ),
                    (
                        self.screener_sb_short,
                        self._safe_indicator_access(self.screener_sb_short),
                    ),
                ]

            # Configure each screener
            all_success = True
            for shorttitle, screener in screeners_to_configure:
                if not screener:
                    open_tv_logger.error(
                        f"Could not find screener indicator: {shorttitle}. Skipping."
                    )
                    all_success = False
                    continue

                try:
                    # Open its settings (retry with overlay dismissal)
                    for click_attempt in range(3):
                        try:
                            screener.click()
                            break
                        except ElementClickInterceptedException:
                            open_tv_logger.warning(
                                f"Overlay blocking screener click (attempt {click_attempt + 1}/3), dismissing..."
                            )
                            # Wait for overlay to disappear, then retry
                            try:
                                WebDriverWait(self.driver, 5).until(
                                    EC.invisibility_of_element_located(
                                        (By.CSS_SELECTOR, "div.screen-otjoFNF2.fade-otjoFNF2")
                                    )
                                )
                            except TimeoutException:
                                # Overlay didn't disappear — try ESC then JS click
                                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                                sleep(1)
                            if click_attempt == 2:
                                # Last resort: JS click bypasses overlays
                                self.driver.execute_script("arguments[0].click();", screener)
                                open_tv_logger.info("Used JS click to bypass overlay")
                    WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                'button[data-qa-id="legend-settings-action"]',
                            )
                        )
                    ).click()
                    settings = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                'div[data-outside-boundary-for="indicator-properties-dialog"]',
                            )
                        )
                    )
                    symbol_inputs = settings.find_elements(
                        By.CSS_SELECTOR,
                        '.inlineRow-uuCuCMOL div[data-name="edit-button"]',
                    )  # symbol inputs

                    # change the symbol inputs based on the total number of symbols
                    for i, to_be_symbol in enumerate(symbols_list):
                        symbol_inputs[i].click()
                        search_input = self.driver.find_element(
                            By.XPATH,
                            '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input',
                        )
                        search_input.send_keys(to_be_symbol)
                        sleep(0.5)  # Wait for search results to populate
                        search_input.send_keys(Keys.ENTER)

                    # click on submit
                    self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
                    open_tv_logger.info(
                        f"Successfully changed the inputs of screener {shorttitle}: {symbols_list}"
                    )
                    sleep(0.5)  # Brief pause for dialog close; callers add their own recalc wait
                except Exception:
                    open_tv_logger.exception(
                        f"Error occurred when filling in the inputs of screener {shorttitle}. Error:"
                    )
                    all_success = False

            return all_success
        except Exception:
            open_tv_logger.exception("Error occurred when configuring screeners. Error:")
            return False

    def open_alerts_sidebar(self):
        """opens the alerts sidebar if it is closed. If it is already open, it does nothing"""
        try:
            alert_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        'div[data-name="right-toolbar"] button[aria-label="Alerts"]',
                    )
                )
            )
            if alert_button.get_attribute("aria-pressed") == "false":
                alert_button.click()
                open_tv_logger.info("Successfully opened the alerts sidebar!")
                return True
            else:  # if the alerts sidebar is already open
                open_tv_logger.info("The alerts sidebar is already open!")
                return True
        except Exception:
            open_tv_logger.exception("An error happened when opening the alerts sidebar. Error: ")
            return False

    def change_candles_type(self, candle_type: str):
        """
        Changes the candle type to `candle_type` if it isn't already so.

        Args:
        candle_type (str): The data-value of the chart style (e.g. "line", "candle").

        Returns:
        bool: True if the candle type was changed successfully, False otherwise.
        """
        try:
            # Check if the desired style is already active via the radiogroup buttons
            style_buttons = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[id="header-toolbar-chart-styles"] button[role="radio"][aria-checked="true"]',
            )
            for btn in style_buttons:
                if btn.get_attribute("data-value") == candle_type.lower():
                    open_tv_logger.info(f"The candle type is already {candle_type}.")
                    return True

            # Try clicking the radio button directly if it exists in the toolbar
            radio_buttons = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[id="header-toolbar-chart-styles"] button[role="radio"]',
            )
            for btn in radio_buttons:
                if btn.get_attribute("data-value") == candle_type.lower():
                    btn.click()
                    open_tv_logger.info(f"Changed candle type to {candle_type} via toolbar button")
                    return True

            # If not in toolbar, open the "Bar's style" dropdown menu
            open_tv_logger.info(f"Changing the style of candles to {candle_type} via dropdown")
            dropdown_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        'div[id="header-toolbar-chart-styles"] button[aria-label="Bar\'s style"]',
                    )
                )
            )
            dropdown_button.click()

            # Wait for the dropdown menu to appear
            menu = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'))
            )

            # Find the desired type by data-value and click on it
            candle_types = menu.find_elements(By.CSS_SELECTOR, 'div[data-role="menuitem"]')
            for c in candle_types:
                if c.get_attribute("data-value") == candle_type.lower():
                    c.click()
                    open_tv_logger.info(f"Changed candle type to {candle_type}!")
                    return True

            open_tv_logger.warning(f"Candle type '{candle_type}' not found in dropdown")
            return False
        except Exception as e:
            open_tv_logger.error(f"Error in changing candle type: {e}")
            return False

    def create_webhook_alert(
        self, indicator_shorttitle: str, webhook_url: str
    ) -> tuple[bool, str | None]:
        """Creates a TradingView alert with webhook notification for the specified indicator.

        IMPORTANT: The indicator must be clicked/selected BEFORE calling this method.
        This ensures the alert dialog opens with the correct indicator pre-selected.

        This method:
        1. Opens the alert creation dialog (indicator should already be selected)
        2. Navigates to the Notifications tab
        3. Ensures the webhook checkbox is enabled
        4. Fills in the webhook URL
        5. Submits the alert

        Args:
            indicator_shorttitle: The short title of the indicator (for logging)
            webhook_url: The URL that TradingView will POST to when the alert triggers

        Returns:
            tuple[bool, str | None]: (success, error_type)
                - (True, None) - Success
                - (False, None) - Generic error
                - (False, "data_subscription") - Data subscription error
                - (False, "condition_invalid") - Screener not in dropdown
        """
        try:
            open_tv_logger.info("create_webhook_alert: opening alert tab...")
            self.utils.open_alert_tab(self.driver)
            open_tv_logger.info("create_webhook_alert: alert tab opened, looking for + button...")

            # Click the + button to open alert creation dialog
            plus_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]'))
            )
            open_tv_logger.info("create_webhook_alert: + button found, clicking...")
            plus_button.click()
            open_tv_logger.info("Clicked on the + button to create webhook alert")

            # Wait for the alert dialog to appear
            try:
                popup = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, 'div[data-qa-id="alerts-create-edit-dialog"]')
                    )
                )
                open_tv_logger.info("Alert creation dialog appeared")
            except TimeoutException:
                open_tv_logger.warning("Alert dialog timeout, refreshing page and retrying...")
                self.driver.get(self.driver.current_url)  # Refresh page
                sleep(3)  # Wait for page to reload

                # Retry opening dialog
                plus_button_retry = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')
                    )
                )
                plus_button_retry.click()
                open_tv_logger.info("Retrying + button click after page refresh")

                popup = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, 'div[data-qa-id="alerts-create-edit-dialog"]')
                    )
                )
                open_tv_logger.info("Alert creation dialog appeared after retry")

            # Validate condition dropdown on Settings tab (default tab when dialog opens)
            if not self._validate_alert_condition(popup, indicator_shorttitle):
                open_tv_logger.error(
                    f"Screener '{indicator_shorttitle}' not available in condition dropdown - likely has runtime error"
                )
                self._close_alert_dialog()
                return (False, "condition_invalid")

            # Step 1: Click the "Webhook >" button to open notifications sub-dialog
            # (TradingView replaced the old tabbed dialog with a button that opens a sub-dialog)
            webhook_nav_btn = WebDriverWait(popup, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[data-qa-id="alert-notifications-button"]')
                )
            )
            webhook_nav_btn.click()
            open_tv_logger.info("Clicked Webhook button to open notifications sub-dialog")

            # Step 2: Wait for the notifications sub-dialog to appear
            notif_dialog = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-qa-id="alerts-notifications-edit-dialog"]')
                )
            )
            open_tv_logger.info("Notifications sub-dialog appeared")

            # Step 3: Ensure the webhook checkbox is checked
            webhook_label = notif_dialog.find_element(
                By.CSS_SELECTOR, 'label[data-qa-id="webhook"]'
            )
            webhook_input = webhook_label.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
            if not webhook_input.get_attribute("checked"):
                webhook_label.click()
                open_tv_logger.info("Enabled webhook checkbox")
            else:
                open_tv_logger.info("Webhook checkbox was already enabled")

            # Step 4: Clear and fill the webhook URL
            webhook_url_input = WebDriverWait(notif_dialog, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input#webhook-url"))
            )
            webhook_url_input.click()
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys("a").key_up(
                Keys.CONTROL
            ).perform()
            webhook_url_input.send_keys(Keys.BACKSPACE)
            webhook_url_input.send_keys(webhook_url)
            open_tv_logger.info(f"Entered webhook URL: {webhook_url}")

            # Step 5: Click "Apply" in the notifications sub-dialog
            apply_button = notif_dialog.find_element(By.CSS_SELECTOR, 'button[data-qa-id="submit"]')
            apply_button.click()
            open_tv_logger.info('Clicked "Apply" in notifications sub-dialog')

            # Step 6: Wait for main dialog to return, then click "Create"
            sleep(0.5)
            main_dialog = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-qa-id="alerts-create-edit-dialog"]')
                )
            )
            submit_button = main_dialog.find_element(By.CSS_SELECTOR, 'button[data-qa-id="submit"]')
            submit_button.click()
            open_tv_logger.info('Clicked "Create" to submit the alert')

            # Check for errors
            try:
                error_element = WebDriverWait(self.driver, 2.5).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            'div[data-qa-id="alerts-create-edit-dialog"] div[data-qa-id="error-hint"]',
                        )
                    )
                )

                # Get error text to determine error type
                error_text = error_element.text.lower()
                open_tv_logger.error(f"Error in alert dialog: {error_text}")

                if "data subscription" in error_text:
                    open_tv_logger.warning("Data subscription error - symbol not available in plan")
                    self._close_alert_dialog()
                    return (False, "data_subscription")

                open_tv_logger.error("Unknown error while creating webhook alert")
                self._close_alert_dialog()
                return (False, None)

            except TimeoutException:
                open_tv_logger.info(
                    f"Webhook alert created successfully for {indicator_shorttitle}"
                )
                return (True, None)

        except Exception:
            open_tv_logger.exception(
                f"Error occurred when creating webhook alert for {indicator_shorttitle}. Error:"
            )
            self._close_alert_dialog()
            return (False, None)

    def _close_alert_dialog(self):
        """Helper method to close the alert creation dialog if it's open."""
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR, 'div[data-qa-id="alerts-create-edit-dialog"]'
            )
            if popup:
                # Try Cancel button first (more reliable)
                cancel_buttons = popup.find_elements(
                    By.CSS_SELECTOR, 'button[name="cancel"][data-qa-id="cancel"]'
                )
                if cancel_buttons:
                    cancel_buttons[0].click()
                    open_tv_logger.info("Closed alert dialog via Cancel button")
                    return

                # Fall back to close (X) button
                close_buttons = popup.find_elements(By.CSS_SELECTOR, 'button[data-name="close"]')
                if close_buttons:
                    close_buttons[0].click()
                    open_tv_logger.info("Closed alert dialog via close button")
                    return

                open_tv_logger.warning("Could not find Cancel or close button in alert dialog")
        except Exception as e:
            open_tv_logger.warning(f"Error closing alert dialog: {e}")

    def _validate_alert_condition(self, popup, indicator_shorttitle: str) -> bool:
        """
        Validates the Condition dropdown shows the screener, not 'Price'.
        If 'Price' is shown, clicks dropdown and selects the screener option.

        Args:
            popup: The alert dialog popup element
            indicator_shorttitle: The short title of the indicator to select

        Returns:
            True if condition is correctly set, False if screener unavailable (runtime error)
        """
        try:
            # Find the condition dropdown on the Settings tab (default tab when dialog opens)
            # Use contains-match on data-qa-id to be resilient to prefix changes
            condition_dropdown = None
            selectors = [
                '[data-qa-id*="main-series-select"]',
                'span[data-qa-id="ui-lib-Input main-series-select"]',
                'span[data-qa-id="ui-kit-disclosure-control main-series-select"]',
            ]

            for selector in selectors:
                try:
                    condition_dropdown = WebDriverWait(popup, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    open_tv_logger.info(f"Found condition dropdown with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not condition_dropdown:
                # Last resort: check if the dialog text already contains the screener name
                dialog_text = popup.text
                if indicator_shorttitle in dialog_text:
                    open_tv_logger.info(
                        f"Condition dropdown selector not found, but dialog text contains '{indicator_shorttitle}' — assuming correct"
                    )
                    return True
                open_tv_logger.error("Could not find condition dropdown with any known selector")
                return False

            # Get current label text from the dropdown button
            current_label = condition_dropdown.text.strip()
            open_tv_logger.info(f"Condition dropdown currently shows: '{current_label}'")

            # Check if already showing the correct screener
            if indicator_shorttitle in current_label:
                open_tv_logger.info(
                    f"Condition dropdown already shows correct screener: '{indicator_shorttitle}'"
                )
                return True

            # Need to select the screener - click dropdown to open options
            open_tv_logger.info(
                f"Condition shows '{current_label}', need to select '{indicator_shorttitle}'"
            )
            condition_dropdown.click()

            # Wait for options menu to appear
            options_menu = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'div[data-qa-id*="popup-menu-container main-series-select"]',
                    )
                )
            )

            # Find all option items
            options = options_menu.find_elements(By.CSS_SELECTOR, 'div[role="option"]')
            open_tv_logger.info(f"Found {len(options)} options in condition dropdown")

            # Search for option containing the screener name
            for option in options:
                option_text = option.text.strip()
                if indicator_shorttitle in option_text:
                    open_tv_logger.info(f"Found matching option: '{option_text}'")
                    option.click()
                    sleep(0.5)  # Brief pause for UI to update
                    return True

            # Screener not found in options - likely has runtime error
            open_tv_logger.error(
                f"Screener '{indicator_shorttitle}' not found in condition dropdown options"
            )
            # Close the dropdown by pressing Escape
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            return False

        except TimeoutException:
            open_tv_logger.error("Timeout waiting for condition dropdown or options menu")
            return False
        except Exception as e:
            open_tv_logger.exception(f"Error validating alert condition: {e}")
            return False

    def indicator_visibility(self, make_visible: bool, shorttitle: str):
        """Makes `shorttitle` indicator visible or hidden by clicking on the indicator's 👁️ button"""
        HIDDEN = "Hidden"
        VISIBLE = "Visible"

        # get the indicator - always get fresh reference
        indicator = self._safe_indicator_access(shorttitle)

        try:
            if indicator is not None:  # that means that we've found our indicator
                eye = indicator.find_element(
                    By.CSS_SELECTOR, 'button[data-qa-id="legend-show-hide-action"]'
                )
                current_visibility = (
                    VISIBLE if "Hide" in eye.get_attribute("aria-label") else HIDDEN
                )

                if make_visible:  # make the indicator visible
                    if current_visibility == HIDDEN:
                        indicator.click()
                        eye.click()
                        open_tv_logger.info(
                            f"Successfully changed the visibility of {shorttitle} to make it visible!"
                        )
                        return True
                    if current_visibility == VISIBLE:
                        open_tv_logger.info(
                            f"{shorttitle} indicator is already visible. No need to change its visibility!"
                        )
                        return True

                if not make_visible:  # make the indicator hidden
                    if current_visibility == VISIBLE:
                        indicator.click()
                        eye.click()
                        open_tv_logger.info(
                            f"Successfully changed the visibility of {shorttitle} to make it hidden!"
                        )
                        return True
                    if current_visibility == HIDDEN:
                        open_tv_logger.info(
                            f"{shorttitle} indicator is already hidden. No need to change its visibility!"
                        )
                        return True
        except Exception:
            open_tv_logger.exception(
                f"Error occurred when changing the visibility of {shorttitle} to make it {'visible' if make_visible else 'hidden'}. Error: "
            )
            return False

        return False

    def is_visible(self, shorttitle: str):
        """This returns `True` if the visibility of `shorttitle` indicator is shown. Otherwise, this returns `False` if its visibility is hidden."""
        # get the indicator - always get fresh reference
        indicator = self._safe_indicator_access(shorttitle)

        # check its visibility
        try:
            if indicator is not None:  # that means that we've found our indicator
                status = "Hidden" if "disabled" in indicator.get_attribute("class") else "Shown"
                open_tv_logger.info(f"{shorttitle} indicator is {status}.")
                return status == "Shown"
        except Exception:
            open_tv_logger.exception(
                f"Error ocurred when checking the visibility of {shorttitle} indicator. Error:"
            )
            return False

        return False

    def is_no_error(self, shorttitle: str):
        """
        this checks if the indicator has successfully loaded without an error. Returns `True` if it has no error but `False` if there is an error.
        """
        try:
            # find the indicator - always get fresh reference to avoid stale element
            indicator = self._safe_indicator_access(shorttitle)

            # ensure the indicator is visible before checking for errors
            if indicator and not self.is_visible(shorttitle):
                open_tv_logger.info(f"Making {shorttitle} visible before checking for errors")
                self.indicator_visibility(True, shorttitle)

            # if there is no error — use stable data-qa-id + class-contains selectors
            # (old hashed classes like statusesWrapper-l31H9iuA broke on TradingView UI updates)
            error_elements = (
                indicator.find_elements(
                    By.CSS_SELECTOR,
                    '[data-qa-id="legend-statuses-wrapper"] [class*="dataProblem"]',
                )
                if indicator
                else ["no indicator"]
            )
            open_tv_logger.info(
                f"is_no_error: error_elements count={len(error_elements)}, indicator found={indicator is not None}"
            )
            if indicator and error_elements == []:
                open_tv_logger.info(f"There is no error in {shorttitle}!")
                return True

            open_tv_logger.error(f"There is an error in {shorttitle}.")
            return False
        except StaleElementReferenceException:
            open_tv_logger.warning(
                f"Stale element when checking error for {shorttitle}, trying to get fresh reference"
            )
            try:
                indicator = self._get_fresh_indicator(shorttitle)
                # ensure the indicator is visible before checking for errors in retry
                if indicator and not self.is_visible(shorttitle):
                    open_tv_logger.info(
                        f"Making {shorttitle} visible before checking for errors (retry)"
                    )
                    self.indicator_visibility(True, shorttitle)

                if (
                    indicator
                    and indicator.find_elements(
                        By.CSS_SELECTOR,
                        '[data-qa-id="legend-statuses-wrapper"] [class*="dataProblem"]',
                    )
                    == []
                ):
                    open_tv_logger.info(f"There is no error in {shorttitle}!")
                    return True
                open_tv_logger.error(f"There is an error in {shorttitle}.")
                return False
            except Exception:
                open_tv_logger.exception(
                    f"Error occurred even after retry for {shorttitle}. Error:"
                )
                return False
        except Exception:
            open_tv_logger.exception(
                f"Error ocurred when checking if {shorttitle} had an error. Error:"
            )
            return False

    def delete_all_alerts(self):
        """Waits for the alert sidebar to show up and checks if there are any alerts. If there are, they are deleted by making all the alerts inactive and then deleting the inactive alerts. Then it waits a second."""

        def open_dropdown():
            """If the dropdown isn't already open, clicks the 3 dots and returns the dropdown that opens"""
            # if the dropdown menu isn't already open
            if not self.driver.find_elements(By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'):
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]')
                    )
                ).click()
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'))
            )

        def find_menu_item(label):
            """Find a dropdown menu item div by its text label.
            Returns the parent item div (for clicking and isDisabled checks)."""
            items = self.driver.find_elements(
                By.XPATH,
                f'//div[@data-qa-id="menu-inner"]/div[.//span[normalize-space(text())="{label}"]]',
            )
            return items[0] if items else None

        try:
            # Make sure that the Alerts tab is open
            self.utils.open_alert_tab(self.driver)

            # Wait briefly for alert list to load (DOM may still be rendering)
            alert_selector = 'div[data-name="alert-item-name"]'
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, alert_selector))
                )
            except Exception:
                found = self.driver.find_elements(By.CSS_SELECTOR, '[data-name^="alert-"]')
                open_tv_logger.debug(
                    f"Alert panel elements found: {[e.get_attribute('data-name') for e in found[:10]]}"
                )
                open_tv_logger.info("There are no alerts. No need to delete any alerts!")
                return True

            # Step 1: Pause all alerts
            open_dropdown()
            pause_btn = find_menu_item("Pause all")
            if not pause_btn:
                # Try legacy label
                pause_btn = find_menu_item("Stop all")
            if pause_btn and "isDisabled" not in (pause_btn.get_attribute("class") or ""):
                pause_btn.click()
                self.utils.click_yes_in_confirm_popup(self.driver)
                open_tv_logger.info("Paused all alerts")
            else:
                open_tv_logger.info("Pause all is disabled or not found — alerts already inactive")

            # Step 2: Delete all inactive alerts
            open_dropdown()
            delete_btn = find_menu_item("Delete all inactive")
            if delete_btn and "isDisabled" not in (delete_btn.get_attribute("class") or ""):
                delete_btn.click()
                self.utils.click_yes_in_confirm_popup(self.driver)
                open_tv_logger.info("Deleted all inactive alerts")
            else:
                open_tv_logger.info(
                    "Delete all inactive is disabled or not found — no inactive alerts"
                )

            open_tv_logger.info("All alerts deleted successfully")
            return True
        except Exception:
            open_tv_logger.exception(
                "Error happened somewhere when deleting all alerts. Failed to delete all alerts. Error:"
            )
            return False

    def get_indicator(self, ind_shorttitle: str):
        """Returns the indicator which has the same shorttitle as `ind_shorttitle`. If an indicator with the same shorttitle can't be found or an error occurs, `None` will be returned"""
        try:
            indicator = None
            sleep(0.5)  # brief DOM stability buffer (WebDriverWait below handles actual waiting)
            wait = WebDriverWait(self.driver, 15)
            indicators = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div[data-qa-id="legend-source-item"]')
                )
            )

            for ind in indicators:
                indicator_name = self.driver.execute_script(
                    'var el = arguments[0].querySelector(\'[data-qa-id*="legend-source-title"]\'); return el ? el.textContent.trim() : "";',
                    ind,
                )
                if indicator_name == ind_shorttitle:
                    open_tv_logger.info(f"Found indicator {ind_shorttitle}!")
                    indicator = ind
                    break
        except Exception:
            # Debug: check why legend items aren't found
            try:
                in_source = "legend-source-item" in self.driver.page_source
                url = self.driver.current_url
                open_tv_logger.error(
                    f"Failed to find indicator {ind_shorttitle}. "
                    f"URL={url}, legend-source-item in page_source={in_source}"
                )
                self.driver.save_screenshot("debug_get_indicator_fail.png")
                open_tv_logger.error("Debug screenshot saved to debug_get_indicator_fail.png")
            except Exception:
                pass
            open_tv_logger.exception(f"Failed to find indicator {ind_shorttitle}. Error:")
            return None

        return indicator

    def _get_fresh_indicator(self, ind_shorttitle: str):
        """Always gets a fresh reference to the indicator to avoid stale element errors"""
        return self.get_indicator(ind_shorttitle)

    def _safe_indicator_access(self, shorttitle: str, max_retries: int = 2):
        """Safely access an indicator with retry logic for stale element exceptions"""
        for attempt in range(max_retries):
            try:
                indicator = self._get_fresh_indicator(shorttitle)
                if indicator:
                    # Test if the element is still valid by accessing a property
                    _ = indicator.get_attribute("class")
                    return indicator
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    open_tv_logger.warning(
                        f"Stale element for {shorttitle}, retrying... (attempt {attempt + 1})"
                    )
                    sleep(1)
                else:
                    open_tv_logger.error(
                        f"Failed to get fresh indicator {shorttitle} after {max_retries} attempts"
                    )
        return None

    def reupload_indicator(self, indicator, indicator_name, indicator_shorttitle):
        """removes indicator and reuploads it again to the chart by clicking on the screener in the Favorites dropdown. It then waits for the indicator to show up on the chart and returns `True` if it does otherwise `False`.

        Don't remove the print statements. It seems like the code will only run with the print statements.
        """
        val = False

        try:
            # Get fresh indicator reference to avoid stale element
            fresh_indicator = self._safe_indicator_access(indicator_shorttitle)
            if not fresh_indicator:
                open_tv_logger.error(f"Could not get fresh reference to {indicator_shorttitle}")
                return False

            # click on the indicator
            fresh_indicator.click()

            # click on data-qa-id="legend-delete-action" (a sub element under the indicator)
            delete_action = WebDriverWait(fresh_indicator, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[data-qa-id="legend-delete-action"]')
                )
            )
            open_tv_logger.debug(f"Found remove button: {delete_action}")
            delete_action.click()

            # click on "Favorites" dropdowm
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        'div[id="header-toolbar-indicators"] button[data-name="show-favorite-indicators"]',
                    )
                )
            ).click()
            open_tv_logger.debug("Favorites dropdown was clicked")

            # Wait for the dropdown menu to appear
            menu = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'))
            )
            open_tv_logger.debug("Dropdown menu appeared")

            # find the indicator in the dropdown menu and click on it
            dropdown_indicators = WebDriverWait(menu, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-role="menuitem"]'))
            )
            for el in dropdown_indicators:
                open_tv_logger.debug(f"Current indicator: {el}")
                text = el.find_element(
                    By.CSS_SELECTOR,
                    'span[class="label-l0nf43ai apply-overflow-tooltip"]',
                ).text
                if indicator_name == text:
                    open_tv_logger.debug(f"Found {indicator_name}")
                    if el.is_displayed():
                        el.click()
                        break
                    else:
                        # Scroll the element into view
                        actions = ActionChains(self.driver).move_to_element(el)
                        actions.perform()
                        el.click()
                        break

            # Wait for the indicator to show up on the chart
            start_time = time()
            timeout = SCREENER_REUPLOAD_TIMEOUT  # max seconds to wait
            while time() - start_time <= timeout:
                # Use _safe_indicator_access to reuse existing selector logic
                reloaded_indicator = self._safe_indicator_access(indicator_shorttitle)
                if reloaded_indicator:
                    val = True
                    open_tv_logger.info(
                        f"{indicator_shorttitle} is on the chart after re-uploading it!"
                    )
                    break
                sleep(1)  # Wait a bit before retrying
        except Exception as e:
            open_tv_logger.exception(
                f"An error occurred when re-uploading {indicator_shorttitle}. Could not reupload {indicator_shorttitle}. Error: {e}"
            )
            return False

        return val

    def current_chart_tframe(self):
        """Returns the current chart's timeframe via the active quick-access button."""
        try:
            active_btns = self.driver.find_elements(
                By.CSS_SELECTOR, '#header-toolbar-intervals button[aria-checked="true"]'
            )
            if active_btns:
                return active_btns[0].get_attribute("aria-label")
            # No quick-access button is active (e.g. 45 seconds is set via dropdown)
            return ""
        except Exception:
            open_tv_logger.exception("Failed to get the current chart timeframe. Error:")
            return ""

    def is_alerts_sidebar_open(self):
        """This checks if the Alerts sidebar is open. Returns `True` if it is and returns `False` if it is not."""
        try:
            alert_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'div[data-name="right-toolbar"] button[aria-label="Alerts"]',
                    )
                )
            )
            if (
                alert_button.get_attribute("aria-pressed") == "true"
            ):  # if the alerts sidebar is open
                open_tv_logger.info("The Alerts sidebar is open!")
                return True
            else:
                open_tv_logger.info("The Alerts sidebar is closed.")
                return False
        except Exception:
            open_tv_logger.exception("Failed to check if the Alerts sidebar is open. Error: ")
            return False

    def no_alerts(self):
        """This checks if there no alerts. If there are no alerts, returns `True` and returns `False` if there are alerts"""
        try:
            self.utils.open_alert_tab(self.driver)  # Make sure that the Alerts tab is open
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-name="alert-item-name"]')
                )
            )
            open_tv_logger.info("There are alerts!")
            return False
        except TimeoutException:
            open_tv_logger.info("There are no alerts!")
            return True
        except Exception:
            open_tv_logger.exception("Failed to check if there are no alerts. Error: ")
            return False
