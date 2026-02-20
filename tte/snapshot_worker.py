"""
Snapshot Worker — Polls Stock Buddy for pending chart snapshots and takes them.

Uses TradingView browser automation to:
1. Switch to "Snapshot" layout (with NWE + Trade Drawer indicators)
2. For each pending setup: change symbol, timeframe, Trade Drawer settings
3. Take chart snapshot → get PNG URL
4. Report result back to Stock Buddy API
"""

import requests
from time import sleep, time

from tte import log
from tte.config import ComboConfig

logger = log.setup_logger(__name__, log.INFO)

# Timeframe mapping: nweTf value → TradingView dropdown label
TF_MAP = {
    "LTF": "1 hour",
    "HTF": "4 hours",
    "1H": "1 hour",
    "4H": "4 hours",
    "H1": "1 hour",
    "H4": "4 hours",
    "1h": "1 hour",
    "4h": "4 hours",
}


class StockBuddyClient:
    """HTTP client for Stock Buddy snapshot API endpoints."""

    def __init__(self, config: ComboConfig):
        self.base_url = config.api_base_url
        self.timeout = config.api_timeout

    def get_pending_snapshots(self, limit: int = 5) -> list[dict]:
        """Fetch pending snapshots from Stock Buddy.

        GET {base_url}/snapshots/pending?limit={limit}
        Returns list of setup dicts, or empty list on error.
        """
        try:
            resp = requests.get(
                f"{self.base_url}/snapshots/pending",
                params={"limit": limit},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            snapshots = data.get("snapshots", [])
            if snapshots:
                logger.info(f"Fetched {len(snapshots)} pending snapshots")
            return snapshots
        except requests.RequestException as e:
            logger.error(f"Failed to fetch pending snapshots: {e}")
            return []

    def update_snapshot(
        self,
        setup_message_id: str,
        snapshot_url: str | None = None,
        snapshot_tv_url: str | None = None,
        error: str | None = None,
    ) -> bool:
        """Report snapshot result back to Stock Buddy.

        POST {base_url}/snapshots/update
        """
        payload: dict = {"setupMessageId": setup_message_id}
        if error:
            payload["error"] = error
        else:
            payload["snapshotUrl"] = snapshot_url
            payload["snapshotTvUrl"] = snapshot_tv_url

        try:
            resp = requests.post(
                f"{self.base_url}/snapshots/update",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(
                f"Failed to update snapshot for {setup_message_id}: {e}"
            )
            return False


class SnapshotWorker:
    """Orchestrates chart snapshot workflow using existing browser automation."""

    def __init__(self, browser, config: ComboConfig, client: StockBuddyClient):
        self.browser = browser
        self.config = config
        self.client = client

    def process_pending_snapshots(self) -> int:
        """Poll for pending snapshots, take them, report results.

        Returns the number of snapshots successfully processed.
        """
        pending = self.client.get_pending_snapshots(self.config.snapshot_batch_size)
        if not pending:
            return 0

        logger.info(f"Processing {len(pending)} pending snapshots")

        # Switch to Snapshot layout
        if not self.browser.change_layout(self.config.snapshot_layout_name):
            logger.error(
                f"Failed to switch to '{self.config.snapshot_layout_name}' layout — aborting snapshot phase"
            )
            return 0

        sleep(2)  # Wait for layout to load

        # Set bar style for snapshots
        self.browser.change_candles_type(self.config.snapshot_bar_style)

        # Ensure legend is visible (needed to double-click Trade Drawer for first setup)
        self._show_legend()

        completed = 0
        for setup in pending:
            try:
                success = self._take_snapshot(setup)
                if success:
                    completed += 1
            except Exception:
                logger.exception(
                    f"Unexpected error processing snapshot for {setup.get('symbol', '?')}"
                )
                self.client.update_snapshot(
                    setup["setupMessageId"], error="Unexpected error"
                )

        # No need to switch back to Screener — maintenance can run on any layout
        # (alert restart + log clear work regardless of current layout)
        logger.info(f"Snapshot phase complete: {completed}/{len(pending)} succeeded")
        return completed

    def _take_snapshot(self, setup: dict) -> bool:
        """Take a chart snapshot for a single setup.

        Steps: change_symbol → change_tframe → change_indicator_settings → save_chart_img
        """
        setup_id = setup["setupMessageId"]
        symbol = setup["symbol"]
        nwe_tf = setup.get("nweTf", "LTF")
        timeframe = TF_MAP.get(nwe_tf, "1 hour")

        logger.info(
            f"Taking snapshot: {symbol} {nwe_tf} ({timeframe}) — "
            f"Entry {setup.get('entryPrice')}, SL {setup.get('stopLoss')}, TP {setup.get('takeProfit')}"
        )

        # 1. Change symbol
        if not self.browser.open_chart.change_symbol(symbol):
            logger.error(f"Failed to change symbol to {symbol}")
            self.client.update_snapshot(setup_id, error="Failed to change symbol")
            return False

        # 2. Change timeframe
        if not self.browser.open_chart.force_change_tframe(timeframe):
            logger.error(f"Failed to change timeframe to {timeframe}")
            self.client.update_snapshot(setup_id, error="Failed to change timeframe")
            return False

        sleep(1)  # Wait for chart to render

        # 3. Show legend (needed to double-click Trade Drawer indicator)
        self._show_legend()

        # 4. Change Trade Drawer indicator settings (v2 — 4 inputs)
        if not self._set_trade_drawer(setup):
            logger.error("Failed to set Trade Drawer settings")
            self.client.update_snapshot(
                setup_id, error="Failed to set Trade Drawer settings"
            )
            return False

        sleep(1)  # Wait for indicator to render

        # 5. Hide indicator legend so it doesn't appear in the snapshot
        self._hide_legend()

        # 6. Take snapshot via Alt+S
        links = self._take_chart_snapshot()

        # 7. Show legend again (ready for next setup)
        self._show_legend()

        if not links:
            logger.error("Failed to take chart snapshot")
            self.client.update_snapshot(
                setup_id, error="Failed to take chart snapshot"
            )
            return False

        # 7. Report success
        self.client.update_snapshot(
            setup_id,
            snapshot_url=links["png"],
            snapshot_tv_url=links["tv"],
        )
        logger.info(f"Snapshot completed for {symbol}: {links['tv']}")
        return True

    def _hide_legend(self):
        """Hide the indicator legend overlay on the chart."""
        from selenium.webdriver.common.by import By

        try:
            toggler = self.browser.driver.find_element(
                By.CSS_SELECTOR, 'button[data-qa-id="legend-toggler"]'
            )
            if toggler.get_attribute("aria-label") == "Hide indicators legend":
                toggler.click()
                sleep(0.3)
                logger.info("Legend hidden")
            else:
                logger.debug("Legend already hidden")
        except Exception:
            logger.debug("Legend toggler not found")

    def _show_legend(self):
        """Show the indicator legend overlay on the chart."""
        from selenium.webdriver.common.by import By

        try:
            toggler = self.browser.driver.find_element(
                By.CSS_SELECTOR, 'button[data-qa-id="legend-toggler"]'
            )
            if toggler.get_attribute("aria-label") == "Show indicators legend":
                toggler.click()
                sleep(0.3)
                logger.info("Legend shown")
            else:
                logger.debug("Legend already visible")
        except Exception:
            logger.debug("Legend toggler not found")

    def _set_trade_drawer(self, setup: dict) -> bool:
        """Set Trade Drawer v2 indicator settings (6 inputs).

        Inputs: entry_time, entry_price, sl, tp1, tp2, tp3
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        drawer_shorttitle = self.config.snapshot_drawer_shorttitle
        driver = self.browser.driver

        try:
            # Double-click Trade Drawer to open settings
            drawer = self.browser.open_chart.get_indicator(drawer_shorttitle)
            if not drawer:
                logger.error(f"Trade Drawer '{drawer_shorttitle}' not found on chart")
                return False

            attempts = 0
            settings = None
            while attempts < 3:
                try:
                    ActionChains(driver).move_to_element(drawer).perform()
                    ActionChains(driver).double_click(drawer).perform()
                    settings = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                'div[data-name="indicator-properties-dialog"]',
                            )
                        )
                    )
                    break
                except Exception:
                    attempts += 1
                    if attempts == 3:
                        logger.error("Failed to open Trade Drawer settings after 3 attempts")
                        return False

            if settings is None:
                return False

            # Click Inputs tab
            inputs_tab = settings.find_element(By.CSS_SELECTOR, 'button[id="inputs"]')
            inputs_tab.click()
            sleep(0.5)

            # Find the 6 numeric input fields using stable data-qa-id selector
            inputs = settings.find_elements(
                By.CSS_SELECTOR, 'input[data-qa-id="ui-lib-Input-input"]'
            )

            logger.info(f"Found {len(inputs)} Trade Drawer inputs")

            if len(inputs) < 4:
                logger.error(
                    f"Expected at least 4 Trade Drawer inputs, found {len(inputs)}"
                )
                # Close dialog
                try:
                    settings.find_element(By.CSS_SELECTOR, 'button[name="cancel"]').click()
                except Exception:
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                return False

            # Map setup data to first 4 inputs only (entry_time, entry_price, sl, tp1)
            # tp2 and tp3 are left unchanged (redundant)
            # alertTimestamp from Stock Buddy is already Unix milliseconds
            alert_ts = setup.get("alertTimestamp", "")
            values = [
                str(alert_ts),                             # entry_time (Unix ms)
                str(setup.get("entryPrice", "")),          # entry_price
                str(setup.get("stopLoss", "")),            # sl
                str(setup.get("takeProfit", "")),          # tp1
            ]

            for i, inp in enumerate(inputs[:4]):
                # Click the input to focus it, then Ctrl+A to select all, then type new value
                inp.click()
                sleep(0.1)
                ActionChains(driver).key_down(Keys.CONTROL, inp).send_keys(
                    "a"
                ).key_up(Keys.CONTROL).perform()
                inp.send_keys(Keys.BACKSPACE)
                inp.send_keys(values[i])

            logger.info(
                f"Trade Drawer settings: time={values[0]}, entry={values[1]}, "
                f"sl={values[2]}, tp1={values[3]}"
            )

            # Submit
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="submit"]'))
            ).click()

            sleep(2)  # Wait for indicator to render
            logger.info("Trade Drawer settings applied")
            return True

        except Exception:
            logger.exception("Failed to set Trade Drawer settings")
            # Try to close any open dialog
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
            return False

    def _take_chart_snapshot(self) -> dict:
        """Take a chart snapshot using Alt+S shortcut.

        Returns {"png": url, "tv": url} on success, or {} on failure.

        Uses Alt+S which copies the snapshot link to clipboard.
        Reads clipboard via JavaScript to avoid interference with user's
        desktop clipboard operations.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        driver = self.browser.driver

        try:
            # Grant clipboard-read permission (required for headless Chrome)
            try:
                driver.execute_cdp_cmd("Browser.grantPermissions", {
                    "permissions": ["clipboardReadWrite", "clipboardSanitizedWrite"],
                    "origin": driver.current_url.split("?")[0],
                })
            except Exception:
                pass  # Non-critical — works without this in non-headless mode

            # Click on the chart to make it active/focused
            chart = driver.find_element(
                By.CSS_SELECTOR, 'div.chart-markup-table'
            )
            ActionChains(driver).click(chart).perform()
            sleep(0.5)

            # Send Alt+S to take snapshot (copies link to clipboard)
            ActionChains(driver).key_down(Keys.ALT).send_keys("s").key_up(
                Keys.ALT
            ).perform()

            logger.info("Sent Alt+S to take snapshot, waiting for clipboard...")
            sleep(2)  # Wait for TradingView to upload and copy link

            # Read clipboard via JavaScript (isolated from desktop clipboard race)
            # Retry a few times in case the upload takes longer
            for attempt in range(5):
                try:
                    clip_text = driver.execute_async_script(
                        """
                        var callback = arguments[arguments.length - 1];
                        navigator.clipboard.readText().then(
                            text => callback(text),
                            err => callback("")
                        );
                        """
                    )
                except Exception:
                    clip_text = ""

                if clip_text and "tradingview.com" in clip_text:
                    # Extract the TV page URL and construct the PNG URL
                    tv_url = clip_text.strip()
                    # TradingView snapshot URLs: https://www.tradingview.com/x/XXXXXXXX/
                    # PNG URLs: https://s3.tradingview.com/snapshots/{prefix}/{id}.png
                    # S3 CDN uses first char (lowercase) as prefix directory
                    snapshot_id = tv_url.rstrip("/").split("/")[-1]
                    prefix = snapshot_id[0].lower()
                    png_url = f"https://s3.tradingview.com/snapshots/{prefix}/{snapshot_id}.png"

                    logger.info(f"Snapshot captured: {tv_url}")
                    return {"png": png_url, "tv": tv_url}

                if attempt < 4:
                    sleep(1)

            logger.error("Failed to get snapshot URL from clipboard after Alt+S")
            return {}

        except Exception:
            logger.exception("Failed to take chart snapshot via Alt+S")
            return {}
