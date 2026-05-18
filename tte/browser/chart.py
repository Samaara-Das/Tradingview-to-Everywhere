"""
this can change the Trade Drawer's settings, change the chart's symbol and timeframe and take a snapshot of the chart.
"""

from time import sleep, time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tte import log

# Set up logger for this file
entry_chart_logger = log.setup_logger(__name__, log.DEBUG)


# class
class OpenChart:
    def __init__(self, driver) -> None:
        self.driver = driver

    def change_indicator_settings(self, drawer_shorttitle, screener_type, entry_object):
        try:
            # double click on the indicator so that the settings can open
            i = 1
            while i <= 3:
                try:
                    drawer_indicator = self.get_indicator(drawer_shorttitle)
                    ActionChains(self.driver).move_to_element(drawer_indicator).perform()
                    ActionChains(self.driver).double_click(drawer_indicator).perform()
                    settings = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                'div[data-name="indicator-properties-dialog"]',
                            )
                        )
                    )
                    break
                except Exception:
                    entry_chart_logger.exception(
                        "Failed to open the Trade Drawer's settings. Error:"
                    )
                    i += 1
                    if i == 4:
                        entry_chart_logger.error(
                            "Trade Drawer indicator's settings failed to open. Could not change the settings. Exiting function."
                        )
                        return False

            # when the settings come up, click on the Inputs tab (just in case we're on some other tab)
            settings.find_element(
                By.CSS_SELECTOR, 'div[class="tabs-vwgPOHG8"] button[id="inputs"]'
            ).click()

            # fill up the settings
            inputs = settings.find_elements(By.CSS_SELECTOR, ".cell-tBgV1m0B input")[:2]
            for i in range(len(inputs)):
                val = ""
                if i == 0:
                    val = screener_type
                elif i == 1:
                    val = str(entry_object)

                ActionChains(self.driver).key_down(Keys.CONTROL, inputs[i]).send_keys("a").perform()
                inputs[i].send_keys(Keys.DELETE)
                inputs[i].send_keys(val)

            entry_chart_logger.info(
                f"Trade Drawer's settings changed. Inputs: screener_type - {screener_type}, entry_object - {entry_object}"
            )

            # click on submit
            self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()

            # wait for the indicator to fully load so that it can take a snapshot of the new entry, sl & tp
            start_time = time()
            timeout = 15  # 15 seconds
            check = False
            sleep(2)
            while time() - start_time <= timeout:
                class_attr = drawer_indicator.get_attribute("class")
                if "Loading" not in class_attr:
                    check = True
                    entry_chart_logger.info("Trade indicator fully loaded!")
                    return True
                else:
                    continue
            if not check:
                entry_chart_logger.error("Trade indicator did not fully load.")
                return False
        except Exception:
            entry_chart_logger.exception("Failed to change the Trade Drawer's settings. Error:")
            return False

    def change_symbol(self, symbol, _attempt: int = 1):
        """Change the chart's symbol to `symbol` if it differs from the current one.

        WS-0 (2026-05-15): the symbol-search interaction occasionally stalls when TV's
        renderer is saturated (Trade Drawer V2 recompute + tick streaming pin the main
        thread). chromedriver returns a urllib3 read-timeout (`Read timed out`).
        On that specific failure we run a single recovery: `driver.refresh()` to flush
        the renderer's queued work, sleep briefly, then retry once. The `_attempt`
        guard caps recursion at 2 total attempts — never loops further.
        """
        try:
            entry_chart_logger.debug(
                f"change_symbol() called with symbol={symbol} (attempt {_attempt})"
            )

            no_exchange_symbol = (
                symbol.split(":")[-1] if ":" in symbol else symbol
            )  # get the symbol without the exchange name (if there is an exchange name)

            entry_chart_logger.debug(f"Stripped symbol: {no_exchange_symbol}")

            symbol_search = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"]')
                )
            )

            current_symbol = symbol_search.find_element(By.CSS_SELECTOR, "span.value-JQZ0HKD4").text
            entry_chart_logger.debug(f"Current chart symbol: {current_symbol}")

            if (
                current_symbol != no_exchange_symbol
            ):  # only search for a specific symbol if the current symbol is different from that symbol
                entry_chart_logger.debug(
                    f"Symbol different, changing from {current_symbol} to {no_exchange_symbol}"
                )

                # Click on Symbol Search button to open popup.
                # JS click bypasses TV's transient overlay (container-VeoIyDt4 et al)
                # that intercepts native clicks on the toolbar from a fresh Chrome
                # session. Falls back to native click if JS path errors.
                try:
                    self.driver.execute_script("arguments[0].click();", symbol_search)
                except Exception:
                    symbol_search.click()
                entry_chart_logger.debug("Clicked symbol search button (JS)")

                # Wait for Symbol Search popup to appear
                symbol_search_dialog = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[data-name="symbol-search-items-dialog"]')
                    )
                )
                entry_chart_logger.debug("Symbol search popup appeared")

                # Find the search input inside the popup
                search_input = symbol_search_dialog.find_element(
                    By.CSS_SELECTOR, 'input[data-qa-id="symbol-search-input"]'
                )
                entry_chart_logger.debug("Found search input field in popup")

                # Select the input (just in case) and clear it
                search_input.click()
                entry_chart_logger.debug("Clicked search input to focus")

                # Select all and delete (Ctrl+A)
                ActionChains(self.driver).key_down(Keys.CONTROL, search_input).send_keys(
                    "a"
                ).key_up(Keys.CONTROL).perform()
                entry_chart_logger.debug("Selected all text (Ctrl+A)")

                # Type the symbol (this will replace selected text)
                search_input.send_keys(symbol)
                entry_chart_logger.debug(f"Typed symbol: {symbol}")

                # Press ENTER to confirm
                search_input.send_keys(Keys.ENTER)
                entry_chart_logger.debug("Pressed ENTER to confirm symbol")

                entry_chart_logger.info(f"Entered symbol {symbol}")

                # Wait for symbol to change in the toolbar
                WebDriverWait(self.driver, 10).until(
                    EC.text_to_be_present_in_element(
                        (
                            By.CSS_SELECTOR,
                            'button[id="header-toolbar-symbol-search"] span.value-JQZ0HKD4',
                        ),
                        no_exchange_symbol,
                    )
                )
                entry_chart_logger.debug(f"Symbol change confirmed in UI: {no_exchange_symbol}")

                # Wait for chart to load
                sleep(1)  # Symbol already confirmed by WebDriverWait; 1s for chart rendering
                entry_chart_logger.debug("Waited 1s for chart to load")

                return True
            else:
                entry_chart_logger.info(
                    f"The current symbol is the same as {no_exchange_symbol}. There is no need to change the symbol!"
                )
                return True
        except Exception as e:
            err_str = str(e)
            # WS-0 retry: detect renderer-stall via the urllib3 read-timeout signature
            # and recover with a full page refresh + one retry. Only on attempt 1.
            # Lowercase substring match so we catch urllib3 variants ("Read timed out",
            # "read timeout", etc.) — code-reviewer flagged exact-case as fragile.
            if "timed out" in err_str.lower() and _attempt == 1:
                entry_chart_logger.warning(
                    "Symbol change hit a renderer-stall read-timeout — refreshing page "
                    "and retrying once."
                )
                try:
                    self.driver.refresh()
                except Exception as refresh_exc:
                    # The renderer is sometimes so saturated that even driver.refresh()
                    # times out — that's just confirmation we couldn't recover this
                    # cycle. Caller treats the False return as "snapshot failed";
                    # the next maintenance tick will retry. No need to dump a full
                    # traceback on every occurrence (noise from 2026-05-18 soak).
                    entry_chart_logger.warning(
                        "Stall-recovery driver.refresh() also timed out (%s) — "
                        "bailing out, next cycle will retry.",
                        type(refresh_exc).__name__,
                    )
                    return False
                sleep(3)  # let TV re-establish its WebSocket + redraw chart
                return self.change_symbol(symbol, _attempt=2)
            entry_chart_logger.exception(f"Failed to change the symbol of the chart. Error: {e}")
            return False

    @staticmethod
    def _get_timeframe_section(timeframe):
        """Map a timeframe label like '45 seconds' to its dropdown section name."""
        tf = timeframe.lower()
        if "tick" in tf:
            return "Ticks"
        elif "second" in tf:
            return "Seconds"
        elif "minute" in tf:
            return "Minutes"
        elif "hour" in tf:
            return "Hours"
        elif "day" in tf:
            return "Days"
        elif "week" in tf:
            return "Weeks"
        elif "month" in tf:
            return "Months"
        elif "range" in tf:
            return "Ranges"
        return ""

    def _open_timeframe_dropdown(self):
        """Click the timeframe dropdown chevron and wait for the menu to render."""
        chevron = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#header-toolbar-intervals > button[aria-label="Chart interval"]')
            )
        )
        try:
            chevron.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", chevron)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'))
        )
        sleep(0.3)

    def _expand_timeframe_section(self, timeframe):
        """Expand the collapsible section (e.g. 'Seconds') that contains `timeframe`."""
        section_name = self._get_timeframe_section(timeframe)
        if section_name:
            section_btns = self.driver.find_elements(
                By.XPATH,
                f'//button[@data-qa-id="ui-lib-title-list-item"][@aria-label="{section_name}"]',
            )
            if section_btns and section_btns[0].get_attribute("aria-expanded") != "true":
                section_btns[0].click()
                sleep(0.3)

    def change_tframe(self, timeframe):
        """Changes the timeframe of the chart to `timeframe`"""
        try:
            # Check if a quick-access button already has this timeframe active
            active_btns = self.driver.find_elements(
                By.CSS_SELECTOR, '#header-toolbar-intervals button[aria-checked="true"]'
            )
            if active_btns and active_btns[0].get_attribute("aria-label") == timeframe:
                entry_chart_logger.info(
                    "No need to change the timeframe as the current chart is already on that timeframe!"
                )
                return True

            # Open the timeframe dropdown via the chevron button
            self._open_timeframe_dropdown()

            # Expand the correct section (Seconds, Minutes, etc.) if collapsed
            self._expand_timeframe_section(timeframe)

            # Find and click the timeframe item
            item = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        f'div[data-qa-id="interval-menu-item"][aria-label="{timeframe}"]',
                    )
                )
            )

            # Already selected — just close the dropdown
            if item.get_attribute("aria-selected") == "true":
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                entry_chart_logger.info(
                    "No need to change the timeframe as the current chart is already on that timeframe!"
                )
                return True

            item.click()
            entry_chart_logger.info(f"Successfully changed the timeframe to {timeframe}!")
            return True
        except Exception:
            entry_chart_logger.exception(
                f"Failed to change the timeframe of the chart to {timeframe}. Error:"
            )
            return False

    def force_change_tframe(self, timeframe):
        """Forces the timeframe change without checking current value first.

        Use this after layout switches where the aria-label might not be accurate.
        Retries once on stale element errors.
        """
        for attempt in range(2):
            try:
                # Open the timeframe dropdown via the chevron button
                self._open_timeframe_dropdown()

                # Expand the correct section if collapsed
                self._expand_timeframe_section(timeframe)

                # Find and click the timeframe item
                item = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            f'div[data-qa-id="interval-menu-item"][aria-label="{timeframe}"]',
                        )
                    )
                )
                item.click()
                entry_chart_logger.info(f"Force changed the timeframe to {timeframe}!")
                return True

            except Exception as e:
                if attempt == 0 and "stale" in str(e).lower():
                    entry_chart_logger.warning("Stale element in force_change_tframe, retrying...")
                    sleep(1)
                    continue
                entry_chart_logger.exception(
                    f"Failed to force change the timeframe to {timeframe}. Error:"
                )
                return False
        return False

    def ensure_regular_hours(self):
        """Ensure the chart session is set to 'Regular trading hours'.

        Opens the session dropdown menu (data-name="session-menu") and clicks
        'Regular trading hours' if it isn't already active. This prevents alerts
        from firing during pre/post-market sessions for stocks.

        Symbols without a session menu (forex, crypto) are unaffected.

        Returns True if regular hours is confirmed, False on error.
        """
        try:
            # Look for the session menu button in the toolbar
            session_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, 'button[data-name="session-menu"]'
            )

            if not session_buttons:
                # No session menu means the symbol doesn't support sessions
                # (e.g., forex, crypto) — this is fine
                entry_chart_logger.info(
                    "No session menu button found (symbol may not support it) — OK"
                )
                return True

            session_btn = session_buttons[0]

            # Check if already on regular hours via the button tooltip/label
            btn_label = session_btn.get_attribute("data-tooltip") or ""
            if btn_label == "Regular trading hours":
                entry_chart_logger.info("Session already set to 'Regular trading hours' — OK")
                return True

            # Click to open the session dropdown menu
            session_btn.click()

            # Wait for the SESSIONS dropdown to appear
            menu = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'))
            )

            # Find and click 'Regular trading hours' in the menu
            items = menu.find_elements(By.CSS_SELECTOR, 'div[data-role="menuitem"]')
            clicked = False
            for item in items:
                label_els = item.find_elements(By.CSS_SELECTOR, "span.label-jFqVJoPk")
                if label_els and label_els[0].text == "Regular trading hours":
                    item.click()
                    clicked = True
                    break

            if clicked:
                sleep(1)  # Wait for chart to reload with regular hours
                entry_chart_logger.info("Set session to 'Regular trading hours'")
                return True
            else:
                entry_chart_logger.warning(
                    "'Regular trading hours' option not found in session menu"
                )
                # Close the menu
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                return False

        except Exception:
            entry_chart_logger.exception("Failed to set regular trading hours:")
            return False

    def save_chart_img(self):
        """Clicks on the camera icon to take a snapshot of the chart and opens it in a new tab. The link of the tab and image are returned in a dictionary. If an error occurs, an empty string is returned.

        Returns
        - Dictionary with keys 'png' and 'tv' if successful, otherwise an empty dictionary.
        """
        png_link = ""
        tv_link = ""
        try:
            camera = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@aria-label='Take a snapshot']/div[@id='header-toolbar-screenshot']",
                    )
                )
            )

            # copy the link of the chart
            camera.click()
            open_in_new_tab = self.driver.find_element(
                By.XPATH,
                '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[5]',
            )
            open_in_new_tab.click()
            entry_chart_logger.info("Took a snapshot and opened it in new tab.")

            # get the url of the newly opened tab after it has fully loaded
            self.driver.switch_to.window(self.driver.window_handles[-1])
            img_element = WebDriverWait(self.driver, 12).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.tv-snapshot-image"))
            )

            # Get the link of the tab and src attribute value of the image
            tv_link = self.driver.current_url
            png_link = img_element.get_attribute("src")
            entry_chart_logger.info("Got link of image and tab!")

            # close the new tab
            self.driver.close()

            # switch back to the original tab
            self.driver.switch_to.window(self.driver.window_handles[0])

        except Exception:
            entry_chart_logger.exception(
                "Failed to save the chart image. Attempting to close new tab if open. Error:"
            )
            # Close the tab that was opened for a snapshot
            if len(self.driver.window_handles) == 2:
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    if "Image" in self.driver.title:
                        entry_chart_logger.info("Closing the snapshot tab")
                        self.driver.close()
                        break

            self.driver.switch_to.window(self.driver.window_handles[0])
            return {}

        return {"png": png_link, "tv": tv_link}

    def get_indicator(self, ind_shorttitle: str):
        """Returns the indicator which has the same shorttitle as `ind_shorttitle`. If an indicator with the same shorttitle can't be found or an error occurrs, `None` will be returned"""
        try:
            indicator = None
            wait = WebDriverWait(self.driver, 15)
            indicators = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div[data-qa-id="legend-source-item"]')
                )
            )

            for ind in indicators:
                # Use JS to get the title text — avoids hashed CSS class selectors
                indicator_name = self.driver.execute_script(
                    """
                    var el = arguments[0].querySelector('[data-qa-id*="legend-source-title"]');
                    return el ? el.textContent.trim() : "";
                    """,
                    ind,
                )
                if indicator_name == ind_shorttitle:
                    entry_chart_logger.info(f"Found indicator {ind_shorttitle}!")
                    indicator = ind
                    break
        except Exception:
            entry_chart_logger.exception(f"Failed to find indicator {ind_shorttitle}. Error:")
            return None

        return indicator
