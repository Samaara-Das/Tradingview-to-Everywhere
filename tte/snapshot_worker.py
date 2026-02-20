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

# Timeframe mapping: setup label → TradingView dropdown label
TF_MAP = {
    "LTF": "1 hour",
    "HTF": "4 hours",
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

        # Switch back to Screener layout
        if not self.browser.change_layout(self.config.layout_name):
            logger.error(
                f"Failed to switch back to '{self.config.layout_name}' layout — "
                "next maintenance cycle will refresh the page"
            )

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

        # 3. Change Trade Drawer indicator settings (v2 — 6 inputs)
        if not self._set_trade_drawer(setup):
            logger.error("Failed to set Trade Drawer settings")
            self.client.update_snapshot(
                setup_id, error="Failed to set Trade Drawer settings"
            )
            return False

        sleep(1)  # Wait for indicator to render

        # 4. Take snapshot
        links = self.browser.open_chart.save_chart_img()
        if not links:
            logger.error("Failed to take chart snapshot")
            self.client.update_snapshot(
                setup_id, error="Failed to take chart snapshot"
            )
            return False

        # 5. Report success
        self.client.update_snapshot(
            setup_id,
            snapshot_url=links["png"],
            snapshot_tv_url=links["tv"],
        )
        logger.info(f"Snapshot completed for {symbol}: {links['tv']}")
        return True

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
            settings.find_element(
                By.CSS_SELECTOR, 'div[class="tabs-vwgPOHG8"] button[id="inputs"]'
            ).click()

            # Get the 6 input fields
            inputs = settings.find_elements(By.CSS_SELECTOR, ".cell-tBgV1m0B input")[:6]
            if len(inputs) < 6:
                logger.error(
                    f"Expected 6 Trade Drawer inputs, found {len(inputs)}. "
                    "Is this Trade Drawer v2?"
                )
                # Close dialog
                driver.find_element(By.CSS_SELECTOR, 'button[name="cancel"]').click()
                return False

            # Map setup data to the 6 inputs
            values = [
                str(setup.get("alertTimestamp", "")),  # entry_time
                str(setup.get("entryPrice", "")),      # entry_price
                str(setup.get("stopLoss", "")),        # sl
                str(setup.get("takeProfit", "")),       # tp1
                "",                                     # tp2 (not used yet)
                "",                                     # tp3 (not used yet)
            ]

            for i, inp in enumerate(inputs):
                ActionChains(driver).key_down(Keys.CONTROL, inp).send_keys(
                    "a"
                ).perform()
                inp.send_keys(Keys.DELETE)
                inp.send_keys(values[i])

            logger.info(
                f"Trade Drawer settings: time={values[0]}, entry={values[1]}, "
                f"sl={values[2]}, tp1={values[3]}"
            )

            # Submit
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="submit"]'))
            ).click()

            # Wait for indicator to load
            start = time()
            sleep(2)
            while time() - start <= 15:
                try:
                    class_attr = drawer.get_attribute("class")
                    if "Loading" not in class_attr:
                        logger.info("Trade Drawer loaded successfully")
                        return True
                except Exception:
                    break  # Element might be stale after settings change
                sleep(0.5)

            # Even if loading check fails, the settings were submitted
            logger.warning("Trade Drawer loading check timed out — proceeding anyway")
            return True

        except Exception:
            logger.exception("Failed to set Trade Drawer settings")
            return False
