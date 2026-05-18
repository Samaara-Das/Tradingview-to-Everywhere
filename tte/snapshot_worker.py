"""
Snapshot Worker — Polls Stock Buddy for pending chart snapshots and takes them.

Uses TradingView browser automation to:
1. Switch to "Snapshot" layout (with Trade Drawer V2 — NWE bands + trade levels)
2. For each pending setup: change symbol, timeframe, Trade Drawer V2 settings
3. Take chart snapshot → get PNG URL
4. Report result back to Stock Buddy API
"""

import contextlib
import threading
from time import sleep, time

import requests

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

    def trigger_backfill(self, days: int = 30) -> bool:
        """Trigger backfill of old setups that lack snapshotStatus field.

        POST {base_url}/snapshots/backfill
        Queues them as "pending" so the worker can process them.
        """
        try:
            resp = requests.post(
                f"{self.base_url}/snapshots/backfill",
                json={"days": days},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            count = data.get("updated", 0)
            if count:
                logger.info(f"Backfill triggered: {count} setups queued for snapshots")
            else:
                logger.info("Backfill: no setups needed queuing")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to trigger snapshot backfill: {e}")
            return False

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
            logger.error(f"Failed to update snapshot for {setup_message_id}: {e}")
            return False


class SnapshotWorker:
    """Orchestrates chart snapshot workflow using existing browser automation."""

    # WS-0 (2026-05-15): after this many snapshots (success or fail), refresh the
    # chart page to flush accumulated DOM + renderer state. Empirically the renderer
    # CPU rises with each symbol switch in a single Chrome session; periodic refresh
    # prevents the slow-creep that triggered the original NSE/NYSE stalls.
    RECYCLE_AFTER_N_SNAPSHOTS = 30

    # WS-0: if change_symbol takes longer than this many seconds before returning
    # False, classify the failure as a renderer stall (distinct from non-stall
    # "Failed to change symbol" causes like the symbol not existing on TV).
    RENDERER_STALL_THRESHOLD_SECONDS = 30.0

    def __init__(
        self,
        browser,
        config: ComboConfig,
        client: StockBuddyClient,
        shutdown_event: threading.Event | None = None,
    ):
        self.browser = browser
        self.config = config
        self.client = client
        self._bars_right_last_set: float = 0
        self._shutdown = shutdown_event
        # WS-0 instrumentation: track consecutive change_symbol failures per symbol
        # so we can fail-fast (skip retry inside the snapshot worker) after the 2nd
        # consecutive stall on the same name.
        self._consec_failures: dict[str, int] = {}
        # WS-0: snapshots taken since the last chart-recycle refresh.
        self._snapshots_since_recycle: int = 0

    def process_pending_snapshots(self) -> int:
        """Poll for pending snapshots, take them, report results.

        Processes up to 2 rounds of batch_size snapshots per cycle to clear
        backlogs faster. Stops when a batch returns fewer than batch_size.

        Returns the total number of snapshots successfully processed.
        """
        max_rounds = 2
        total_completed = 0

        # Login-state guard (2026-05-14): the long-running Chrome can lose its TV session
        # silently, leaving an owner-only chart layout showing the "Chart Not Found" placeholder
        # page. Every selector then times out. Recover before processing any snapshots.
        if not self.browser.ensure_chart_layout_loaded():
            logger.error(
                "Chart layout unavailable — skipping snapshot round. Will retry on next cycle."
            )
            return 0

        for round_num in range(max_rounds):
            pending = self.client.get_pending_snapshots(self.config.snapshot_batch_size)
            if not pending:
                break

            logger.info(
                f"Processing {len(pending)} pending snapshots (round {round_num + 1}/{max_rounds})"
            )

            # One-time setup on first round only
            if round_num == 0:
                # Set "bars to right" margin (once at startup, then every 24h)
                if time() - self._bars_right_last_set > 86400:
                    self._set_bars_to_right()

                # Set bar style for snapshots
                self.browser.change_candles_type(self.config.snapshot_bar_style)

                # Ensure legend is visible (needed to double-click Trade Drawer)
                self._show_legend()

            completed = 0
            for setup in pending:
                if self._shutdown and self._shutdown.is_set():
                    logger.info("Shutdown requested — stopping snapshot processing")
                    total_completed += completed
                    return total_completed
                try:
                    success = self._take_snapshot(setup)
                    if success:
                        completed += 1
                except Exception:
                    logger.exception(
                        f"Unexpected error processing snapshot for {setup.get('symbol', '?')}"
                    )
                    self.client.update_snapshot(setup["setupMessageId"], error="Unexpected error")
                    # Clean up after failure to prevent cascading failures
                    self._dismiss_dialogs()
                    self._show_legend()

                # WS-0 chart-recycle: every N snapshots, refresh the chart to flush
                # accumulated renderer state. Cheap relative to chart load time and
                # measurably reduces the per-symbol stall rate.
                self._snapshots_since_recycle += 1
                if self._snapshots_since_recycle >= self.RECYCLE_AFTER_N_SNAPSHOTS:
                    self._recycle_chart()
                    self._snapshots_since_recycle = 0

            total_completed += completed
            logger.info(f"Round {round_num + 1}: {completed}/{len(pending)} succeeded")

            # If fewer than batch_size returned, no more pending — stop
            if len(pending) < self.config.snapshot_batch_size:
                break

        if total_completed:
            logger.info(f"Snapshot phase complete: {total_completed} total succeeded")
        return total_completed

    def _recycle_chart(self):
        """Refresh the TV chart page to flush accumulated renderer/DOM state.

        WS-0 (2026-05-15): chrome's renderer slowly accumulates load as TTE switches
        through symbols (each switch adds tooltips, indicator state, etc.). After
        ~30 symbol switches the renderer can hit a sustained ~93% CPU and Selenium
        clicks start timing out. A page refresh is cheap (~5-10s) compared to the
        cost of a hung snapshot and resets the renderer cleanly. We also need to
        re-run the per-cycle setup (legend visible, bar style, bars-to-right) on
        the next round, so we just zero the bars-right marker too.
        """
        try:
            logger.info(f"Chart recycled after {self.RECYCLE_AFTER_N_SNAPSHOTS} snapshots")
            self.browser.driver.refresh()
            sleep(5)  # let TV re-establish its WebSocket + redraw the chart
            # Force the per-round setup to re-run on the next round.
            self._bars_right_last_set = 0
            # Defensive: ensure the chart layout is back (refresh can occasionally
            # leave the placeholder page if the session was wobbly).
            if not self.browser.ensure_chart_layout_loaded():
                logger.warning(
                    "Chart layout not back after recycle refresh — will retry next cycle."
                )
        except Exception:
            logger.exception("Failed to recycle chart; continuing without refresh.")

    def _dismiss_dialogs(self):
        """Close any leftover dialogs from a failed snapshot.

        Checks for specific dialog types and clicks cancel/close. Falls back
        to ESC only if a dialog is detected but has no cancel button.
        Prevents cascading failures when one snapshot leaves a dialog open.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        driver = self.browser.driver
        dialog_selectors = [
            'div[data-name="indicator-properties-dialog"]',
            'div[data-name="series-properties-dialog"]',
        ]
        for selector in dialog_selectors:
            try:
                dialogs = driver.find_elements(By.CSS_SELECTOR, selector)
                if not dialogs:
                    continue
                # Try clicking cancel button
                cancel = dialogs[0].find_elements(By.CSS_SELECTOR, 'button[name="cancel"]')
                if cancel:
                    cancel[0].click()
                    sleep(0.2)
                    logger.info(f"Dismissed leftover dialog: {selector}")
                    return
                # Fallback: ESC (only if dialog was found but no cancel button)
                dialogs[0].send_keys(Keys.ESCAPE)
                sleep(0.2)
                logger.info(f"Dismissed dialog via ESC: {selector}")
                return
            except Exception:
                continue

    def _take_snapshot(self, setup: dict) -> bool:
        """Take a chart snapshot for a single setup.

        Steps: dismiss_dialogs → change_symbol → change_tframe →
               change_indicator_settings → save_chart_img
        """
        # Dismiss any leftover dialogs from previous failed snapshot
        self._dismiss_dialogs()

        setup_id = setup["setupMessageId"]
        symbol = setup.get("full_symbol", setup["symbol"])
        nwe_tf = setup.get("nweTf", "LTF")
        timeframe = TF_MAP.get(nwe_tf, "1 hour")

        logger.info(
            f"Taking snapshot: {symbol} {nwe_tf} ({timeframe}) — "
            f"Entry {setup.get('entryPrice')}, SL {setup.get('stopLoss')}, TP {setup.get('takeProfit')}"
        )

        # WS-0 fail-fast: if a symbol has already failed twice in a row, skip it
        # outright on this poll cycle. Stock Buddy will keep the doc in `pending`
        # so the next cycle (or post-recycle attempt) gets a clean shot at it.
        if self._consec_failures.get(symbol, 0) >= 2:
            logger.warning(
                f"Skipping {symbol} — failed {self._consec_failures[symbol]} times in a row; "
                "deferring to next cycle."
            )
            self.client.update_snapshot(setup_id, error="renderer_stall_skipped")
            return False

        # 1. Change symbol — WS-0 time it so we can classify renderer stalls vs other failures.
        change_symbol_start = time()
        change_symbol_ok = self.browser.open_chart.change_symbol(symbol)
        change_symbol_elapsed = time() - change_symbol_start
        if not change_symbol_ok:
            # WS-0 classification: a stall is a slow failure (renderer was busy and the
            # urllib3 read timeout fired); a non-stall is a fast failure (symbol not on TV,
            # selector broken, etc.). Tag distinctly so SB can see the difference.
            if change_symbol_elapsed >= self.RENDERER_STALL_THRESHOLD_SECONDS:
                error_tag = "renderer_stall"
                logger.error(
                    f"Failed to change symbol to {symbol} after {change_symbol_elapsed:.1f}s — "
                    "classifying as renderer_stall."
                )
            else:
                error_tag = "Failed to change symbol"
                logger.error(
                    f"Failed to change symbol to {symbol} in {change_symbol_elapsed:.1f}s "
                    "(not a stall)."
                )
            self._consec_failures[symbol] = self._consec_failures.get(symbol, 0) + 1
            self.client.update_snapshot(setup_id, error=error_tag)
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
            self.client.update_snapshot(setup_id, error="Failed to set Trade Drawer settings")
            return False

        sleep(4)  # Wait for NWE + candles + trade levels to render (bumped 2→4 on 2026-05-08)

        # 5. Hide indicator legend so it doesn't appear in the snapshot
        self._hide_legend()

        # 6. Click chart and press Alt+R to auto-fit/reset scale
        self._auto_fit_chart()

        # 7. Take snapshot via Alt+S
        links = self._take_chart_snapshot()

        # 8. Show legend again (ready for next setup)
        self._show_legend()

        if not links:
            logger.error("Failed to take chart snapshot")
            self.client.update_snapshot(setup_id, error="Failed to take chart snapshot")
            return False

        # 7. Report success — and reset the WS-0 consecutive-failure counter for this
        # symbol since the snapshot landed cleanly.
        self._consec_failures.pop(symbol, None)
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
                sleep(0.1)
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
                sleep(0.1)
                logger.info("Legend shown")
            else:
                logger.debug("Legend already visible")
        except Exception:
            logger.debug("Legend toggler not found")

    def _auto_fit_chart(self):
        """Click chart to focus it, then press Alt+R to reset/auto-fit the scale."""
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        driver = self.browser.driver
        try:
            chart = driver.find_element(By.CSS_SELECTOR, "div.chart-markup-table")
            ActionChains(driver).click(chart).perform()
            sleep(0.1)
            ActionChains(driver).key_down(Keys.ALT).send_keys("r").key_up(Keys.ALT).perform()
            sleep(0.7)  # Wait for chart to re-render
            logger.info("Chart auto-fit (Alt+R) applied")
        except Exception:
            logger.warning("Failed to auto-fit chart via Alt+R — continuing anyway")

    def _set_bars_to_right(self):
        """Set 'Bars to the right' via chart settings dialog (right margin for drawings)."""
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.wait import WebDriverWait

        driver = self.browser.driver
        bars_value = str(self.config.snapshot_bars_to_right)

        try:
            # 1. Right-click chart area to open context menu
            chart = driver.find_element(By.CSS_SELECTOR, "div.chart-markup-table")
            ActionChains(driver).context_click(chart).perform()
            sleep(0.3)

            # 2. Wait for context menu
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa-id="menu-inner"]'))
            )

            # 3. Click "Settings..." row
            menu_items = driver.find_elements(By.CSS_SELECTOR, 'span[data-label="true"]')
            settings_clicked = False
            for item in menu_items:
                if "Settings" in item.text:
                    item.click()
                    settings_clicked = True
                    break
            if not settings_clicked:
                logger.warning("Could not find 'Settings...' in context menu")
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                return

            # 4. Wait for chart settings dialog
            dialog = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-name="series-properties-dialog"]')
                )
            )
            sleep(0.3)

            # 5. Click "Canvas" tab
            canvas_tab = dialog.find_element(By.CSS_SELECTOR, 'button[data-name="canvas"]')
            canvas_tab.click()
            sleep(0.3)

            # 6. Find and fill "paneRightMargin" input
            margin_input = dialog.find_element(
                By.CSS_SELECTOR, 'input[data-name="paneRightMargin"]'
            )
            margin_input.click()
            sleep(0.1)
            ActionChains(driver).key_down(Keys.CONTROL, margin_input).send_keys("a").key_up(
                Keys.CONTROL
            ).perform()
            margin_input.send_keys(Keys.BACKSPACE)
            margin_input.send_keys(bars_value)

            # 7. Click submit to save
            dialog.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
            sleep(0.5)

            self._bars_right_last_set = time()
            logger.info(f"Set bars to right: {bars_value}")

        except Exception:
            logger.warning("Failed to set bars to right — continuing anyway", exc_info=True)
            with contextlib.suppress(Exception):
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()

    def _wait_for_indicator_ready(self, shorttitle: str, element, timeout: float = 3.5):
        """Wait up to `timeout` seconds for a legend-source-item to finish loading.

        Polls every 200ms, checking data-status != "loading" on the element.
        Re-fetches the element on StaleElementReferenceException.

        Returns the (possibly re-fetched) element when ready, or the last known
        element if the timeout is exceeded (caller proceeds with a warning).
        """
        from selenium.common.exceptions import StaleElementReferenceException

        deadline = time() + timeout
        current = element
        while time() < deadline:
            try:
                status = current.get_attribute("data-status")
                if status != "loading":
                    logger.debug(f"Indicator '{shorttitle}' ready (data-status={status!r})")
                    return current
            except StaleElementReferenceException:
                current = self.browser.open_chart.get_indicator(shorttitle)
                if current is None:
                    sleep(0.2)
                    continue
            sleep(0.2)

        logger.warning(
            f"Indicator '{shorttitle}' still loading after {timeout}s — proceeding anyway"
        )
        return current

    def _set_trade_drawer(self, setup: dict) -> bool:
        """Set Trade Drawer v2 indicator settings (6 inputs).

        Inputs: entry_time, entry_price, sl, tp1, tp2, tp3
        """
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.wait import WebDriverWait

        drawer_shorttitle = self.config.snapshot_drawer_shorttitle
        driver = self.browser.driver

        try:
            # Double-click Trade Drawer to open settings
            drawer = self.browser.open_chart.get_indicator(drawer_shorttitle)
            if not drawer:
                logger.error(f"Trade Drawer '{drawer_shorttitle}' not found on chart")
                return False

            # Wait for indicator to finish loading before interacting
            drawer = self._wait_for_indicator_ready(drawer_shorttitle, drawer, timeout=3.5)
            if not drawer:
                logger.error(f"Trade Drawer '{drawer_shorttitle}' not found after loading wait")
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
            sleep(0.3)

            # Find the 6 numeric input fields using stable data-qa-id selector
            inputs = settings.find_elements(
                By.CSS_SELECTOR, 'input[data-qa-id="ui-lib-Input-input"]'
            )

            logger.info(f"Found {len(inputs)} Trade Drawer inputs")

            if len(inputs) < 4:
                logger.error(f"Expected at least 4 Trade Drawer inputs, found {len(inputs)}")
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
            sl_value = setup.get("stopLoss", "")
            tp_value = setup.get("takeProfit", "")
            # Reversed-strategy visual: draw TP where SL is and SL where TP is.
            # Webhook payload to Stock Buddy is unchanged — only the chart drawing flips.
            if getattr(self.config, "reversed_strategy_snapshots", False):
                sl_value, tp_value = tp_value, sl_value
            values = [
                str(alert_ts),  # entry_time (Unix ms)
                str(setup.get("entryPrice", "")),  # entry_price
                str(sl_value),  # sl
                str(tp_value),  # tp1
            ]

            for i, inp in enumerate(inputs[:4]):
                # Click the input to focus it, then Ctrl+A to select all, then type new value
                inp.click()
                sleep(0.1)
                ActionChains(driver).key_down(Keys.CONTROL, inp).send_keys("a").key_up(
                    Keys.CONTROL
                ).perform()
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

            # Wait for indicator to recompile and re-render after settings apply.
            # Bumped 2s → 5s on 2026-05-08 after the reversed Trade Drawer V2 deploy:
            # tte-1 was failing snapshots with the new Pine even though Sammy
            # confirmed it draws correctly when given more time. Manager hypothesis:
            # the new shorter Pine source applies faster, but the indicator's
            # internal redraw or input-validation cycle still needs ~3-5s before
            # the chart is in a snapshottable state.
            sleep(5)
            logger.info("Trade Drawer settings applied")
            return True

        except Exception:
            logger.exception("Failed to set Trade Drawer settings")
            # Try to close any open dialog
            with contextlib.suppress(Exception):
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return False

    def _take_chart_snapshot(self) -> dict:
        """Take a chart snapshot using Alt+S shortcut.

        Returns {"png": url, "tv": url} on success, or {} on failure.

        Uses Alt+S which copies the snapshot link to clipboard.
        Reads clipboard via JavaScript to avoid interference with user's
        desktop clipboard operations.
        """
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        driver = self.browser.driver

        try:
            # Grant clipboard-read permission (required for headless Chrome)
            try:
                driver.execute_cdp_cmd(
                    "Browser.grantPermissions",
                    {
                        "permissions": ["clipboardReadWrite", "clipboardSanitizedWrite"],
                        "origin": driver.current_url.split("?")[0],
                    },
                )
            except Exception:
                pass  # Non-critical — works without this in non-headless mode

            # Click on the chart to make it active/focused
            chart = driver.find_element(By.CSS_SELECTOR, "div.chart-markup-table")
            ActionChains(driver).click(chart).perform()
            sleep(0.2)

            # Send Alt+S to take snapshot (copies link to clipboard)
            ActionChains(driver).key_down(Keys.ALT).send_keys("s").key_up(Keys.ALT).perform()

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
                    sleep(0.7)

            logger.error("Failed to get snapshot URL from clipboard after Alt+S")
            return {}

        except Exception:
            logger.exception("Failed to take chart snapshot via Alt+S")
            return {}
