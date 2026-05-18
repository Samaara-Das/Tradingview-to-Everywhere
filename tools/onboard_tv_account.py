"""
WS-D — Onboard a brand-new TradingView account for use with a TTE container.

Reuses the existing `Browser` infrastructure (cookie-injected first login,
post-login chart configuration) plus a small set of NEW Selenium primitives
that don't exist yet in tte/browser/tradingview.py:

  1. Paste a Pine Script source into Pine Editor and save+add-to-chart.
  2. Favorite (star) an indicator from "My Scripts" so reupload_indicator()
     can find it under Favorites later.
  3. Create a NEW named layout (different from `save_layout()` which
     overwrites the current name).
  4. Set theme to dark (whole-app preference).
  5. Set chart properties (bars-to-right, auto-scale, etc.) — extend the
     existing `_set_bars_to_right` Canvas-tab flow.

The full sequence per `.claude/specs/ws-d-bootstrap-plan.md` §"Settings sequence":

   1. Inject cookies → start container (one-shot — `inject_tv_cookies.py`)
   2. Open chart → verify session via `is_chart_layout_loaded()`
   3. Set theme dark
   4. Open Pine Editor → paste Screener V2 → save → add to chart
   5. Star Screener V2 in My Scripts
   6. Save layout as "Screener" (45s, candle)
   7. Open Pine Editor → paste Trade Drawer V2 → save → add to chart
   8. Star Trade Drawer V2
   9. Switch to a blank chart, set Canvas-tab properties
  10. Save layout as "Snapshot"
  11. Open alerts sidebar (already in setup_tv)
  12. Hand off to main TTE flow

USAGE:
  pipenv run python tools/onboard_tv_account.py \\
      --email <tv-email> \\
      --user-data-dir <isolated-chrome-profile-dir> \\
      --instance tte-2 \\
      [--dry-run]

PREREQUISITES (gating real runs):
  1. `inject_tv_cookies.py` was already run with TV_SESSION_ID + TV_SESSION_ID_SIGN
     so the target user-data-dir has a logged-in session.
  2. Selectors below are placeholders — they MUST be verified via
     claude-in-chrome MCP on a live TV chart page before this script is run
     end-to-end. See the TODO markers.

The script is wired up but NOT exercised end-to-end in this PR — selector
discovery + a Rahul-cookies live run are the next step.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tte import log
from tte.browser.tradingview import Browser
from tte.config import ComboConfig

logger = log.setup_logger(__name__, log.INFO)

REPO_ROOT = Path(__file__).parent.parent
PINE_SCREENER = REPO_ROOT / "Pine Script Code" / "TTE Screener V2.txt"
PINE_TRADE_DRAWER = REPO_ROOT / "Pine Script Code" / "Trade Drawer V2.txt"


@dataclass
class OnboardConfig:
    email: str
    user_data_suffix: str
    instance: str
    dry_run: bool

    @property
    def screener_layout(self) -> str:
        return "Screener"

    @property
    def snapshot_layout(self) -> str:
        return "Snapshot"


# ---------------------------------------------------------------------------
# Selector constants — VERIFY VIA claude-in-chrome MCP BEFORE RUNNING
# ---------------------------------------------------------------------------
# These are best-guess placeholders inferred from the WS-D bootstrap plan.
# Discovery process: open https://www.tradingview.com/chart/ in Sammy's
# logged-in Chrome via claude-in-chrome MCP, locate each element with
# evaluate_script(`document.querySelector('...')`), confirm uniqueness, then
# update the constant below. TODO markers flag every one that needs this pass.

# Pine Editor — bottom tab opener
SEL_PINE_EDITOR_TAB = 'button[data-name="pine-editor-pane"]'  # TODO verify
# Monaco editor textarea inside Pine Editor
SEL_PINE_MONACO = "div.monaco-editor textarea"  # TODO verify
# Pine Editor "Save" toolbar button
SEL_PINE_SAVE = 'button[data-name="save"]'  # TODO verify
# Save-as dialog title input (when a Pine source is saved for the first time)
SEL_PINE_SAVE_DIALOG_TITLE = 'input[name="title"]'  # TODO verify
SEL_PINE_SAVE_DIALOG_CONFIRM = 'button[data-name="save"]'  # TODO verify
# Pine Editor "Add to chart" button
SEL_PINE_ADD_TO_CHART = 'button[data-name="add-to-chart"]'  # TODO verify

# Indicators dialog — "My Scripts" tab
SEL_INDICATOR_BUTTON = 'div[id="header-toolbar-indicators"]'
SEL_INDICATOR_MY_SCRIPTS_TAB = 'div[data-name="indicator-tab-my_scripts"]'  # TODO verify
SEL_INDICATOR_ROW_BY_TITLE = (
    "div[role='row'] span[title='{title}']"  # TODO verify; format with .format(title=...)
)
SEL_INDICATOR_ROW_STAR = (
    "div[role='row']:has(span[title='{title}']) span.favorite-icon"  # TODO verify
)

# Save layout-as flow
SEL_SAVE_LOAD_MENU = 'button[data-name="save-load-menu"]'  # TODO verify
SEL_SAVE_LAYOUT_AS = 'div[data-name="save-as"]'  # TODO verify
SEL_LAYOUT_NAME_INPUT = 'input[data-name="layout-name"]'  # TODO verify
SEL_LAYOUT_SAVE_CONFIRM = 'button[data-name="confirm-save"]'  # TODO verify

# Theme — User menu → Settings → Appearance
SEL_USER_MENU_BUTTON = 'button[aria-label="Open user menu"]'  # TODO verify
SEL_USER_MENU_SETTINGS = 'div[data-name="header-user-menu-settings"]'  # TODO verify
SEL_SETTINGS_APPEARANCE_TAB = 'div[data-name="settings-tab-appearance"]'  # TODO verify
SEL_SETTINGS_COLOR_THEME_DARK = 'label[data-name="color-theme-dark"] input'  # TODO verify
SEL_SETTINGS_OK = 'button[data-name="submit"]'  # TODO verify


# ---------------------------------------------------------------------------
# Onboarding primitives
# ---------------------------------------------------------------------------


def _wait(driver, selector: str, timeout: int = 20):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


def _click(driver, selector: str, timeout: int = 20):
    el = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    el.click()
    return el


def set_theme_dark(browser: Browser) -> bool:
    """Open user menu → Settings → Appearance, switch theme to Dark."""
    driver = browser.driver
    try:
        _click(driver, SEL_USER_MENU_BUTTON)
        _click(driver, SEL_USER_MENU_SETTINGS)
        _click(driver, SEL_SETTINGS_APPEARANCE_TAB)
        _click(driver, SEL_SETTINGS_COLOR_THEME_DARK)
        _click(driver, SEL_SETTINGS_OK)
        logger.info("Theme set to dark")
        return True
    except (TimeoutException, Exception) as e:
        logger.error(f"set_theme_dark failed: {e}")
        return False


def paste_pine_source(browser: Browser, source_path: Path, title: str) -> bool:
    """Open Pine Editor, paste source from a file, save with `title`, add to chart.

    Uses Monaco editor — pasting via JS is more reliable than `send_keys` for
    long sources. The 600-line Pine sources timeout `send_keys`; we set the
    editor model value via `editor.setValue` then save.
    """
    driver = browser.driver
    if not source_path.exists():
        logger.error(f"Pine source not found: {source_path}")
        return False

    source = source_path.read_text(encoding="utf-8")
    try:
        _click(driver, SEL_PINE_EDITOR_TAB)
        time.sleep(1.0)
        # Use the Monaco JS API to set the editor value in one operation.
        # `monaco.editor.getEditors()[0]` is the standard hook.
        driver.execute_script("monaco.editor.getEditors()[0].setValue(arguments[0]);", source)
        time.sleep(0.5)
        _click(driver, SEL_PINE_SAVE)
        # First-save dialog: enter the title
        _wait(driver, SEL_PINE_SAVE_DIALOG_TITLE)
        title_input = driver.find_element(By.CSS_SELECTOR, SEL_PINE_SAVE_DIALOG_TITLE)
        title_input.clear()
        title_input.send_keys(title)
        _click(driver, SEL_PINE_SAVE_DIALOG_CONFIRM)
        time.sleep(1.0)
        _click(driver, SEL_PINE_ADD_TO_CHART)
        logger.info(f"Pine source '{title}' saved and added to chart")
        return True
    except (TimeoutException, Exception) as e:
        logger.error(f"paste_pine_source('{title}') failed: {e}")
        return False


def favorite_indicator(browser: Browser, title: str) -> bool:
    """Star an indicator in My Scripts so it appears in Favorites later."""
    driver = browser.driver
    try:
        _click(driver, SEL_INDICATOR_BUTTON)
        _click(driver, SEL_INDICATOR_MY_SCRIPTS_TAB)
        time.sleep(0.5)
        star_selector = SEL_INDICATOR_ROW_STAR.format(title=title)
        _click(driver, star_selector)
        # Close the indicators dialog
        driver.find_element(By.CSS_SELECTOR, "body").send_keys(Keys.ESCAPE)
        logger.info(f"Indicator '{title}' favorited")
        return True
    except (TimeoutException, Exception) as e:
        logger.error(f"favorite_indicator('{title}') failed: {e}")
        return False


def save_layout_as(browser: Browser, name: str) -> bool:
    """Create a NEW named layout (distinct from `save_layout()` overwrite-current)."""
    driver = browser.driver
    try:
        _click(driver, SEL_SAVE_LOAD_MENU)
        _click(driver, SEL_SAVE_LAYOUT_AS)
        name_input = _wait(driver, SEL_LAYOUT_NAME_INPUT)
        name_input.clear()
        name_input.send_keys(name)
        _click(driver, SEL_LAYOUT_SAVE_CONFIRM)
        logger.info(f"Layout saved as '{name}'")
        return True
    except (TimeoutException, Exception) as e:
        logger.error(f"save_layout_as('{name}') failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_onboarding(cfg: OnboardConfig) -> int:
    """Execute the 11-step bootstrap sequence."""
    logger.info(
        f"WS-D onboarding START | email={cfg.email} | instance={cfg.instance} "
        f"| dry_run={cfg.dry_run}"
    )

    if cfg.dry_run:
        logger.info("[DRY-RUN] Steps that would execute:")
        logger.info("  1. Verify cookie-injection (chart loaded as logged-in)")
        logger.info("  2. Set theme dark")
        logger.info("  3. Paste Screener V2 Pine + save + add-to-chart")
        logger.info("  4. Favorite Screener V2 in My Scripts")
        logger.info(f"  5. Save layout as '{cfg.screener_layout}'")
        logger.info("  6. Paste Trade Drawer V2 Pine + save + add-to-chart")
        logger.info("  7. Favorite Trade Drawer V2")
        logger.info(f"  8. Save layout as '{cfg.snapshot_layout}'")
        logger.info("  9. Open alerts sidebar (via setup_tv)")
        logger.info(" 10. Sanity-check chart loaded; hand off")
        logger.info("[DRY-RUN] Pass --commit (live mode flag) to execute.")
        return 0

    # 0. Construct a Browser instance bound to the target user-data-dir.
    cfg_inst = ComboConfig()
    browser = Browser(
        keep_open=True,
        user_data_suffix=cfg.user_data_suffix,
        screener_shorttitle=cfg_inst.screener_shorttitle,
        screener_name=cfg_inst.screener_name,
        drawer_shorttitle="",
        drawer_name="",
        interval_minutes=cfg_inst.maintenance_interval // 60,
        start_fresh=False,
        screener_ob_short=cfg_inst.screener_shorttitle,
        screener_ob_name=cfg_inst.screener_name,
        screener_nw_short=cfg_inst.screener_shorttitle,
        screener_nw_name=cfg_inst.screener_name,
        screener_sb_short=cfg_inst.screener_shorttitle,
        screener_sb_name=cfg_inst.screener_name,
        mode="combo",
        layout_name=cfg.screener_layout,
        chart_timeframe="45 seconds",
        bar_style="candle",
        headless=False,  # onboarding wants a visible window for manual diagnosis
    )
    if not browser.init_succeeded:
        logger.error("Browser init failed — aborting onboarding")
        return 2

    # 1. Cookie-injection prerequisite: chart should load as a logged-in user.
    if not browser.ensure_chart_layout_loaded():
        logger.error(
            "Chart layout not detected; cookie injection may have failed. "
            "Run inject_tv_cookies.py before retrying."
        )
        return 3

    # 2. Theme dark
    if not set_theme_dark(browser):
        logger.warning("Theme set failed — continuing (cosmetic)")

    # 3. Paste Screener V2 and add to chart
    if not paste_pine_source(browser, PINE_SCREENER, "TTE Screener V2"):
        logger.error("Screener V2 Pine paste failed — aborting")
        return 4

    # 4. Favorite Screener V2
    if not favorite_indicator(browser, "TTE Screener V2"):
        logger.warning("Favoriting Screener V2 failed — manual fix needed before tte-N runs")

    # 5. Save layout as "Screener"
    if not save_layout_as(browser, cfg.screener_layout):
        logger.error(f"Save layout '{cfg.screener_layout}' failed")
        return 5

    # 6. Paste Trade Drawer V2 and add to chart
    if not paste_pine_source(browser, PINE_TRADE_DRAWER, "Trade Drawer V2"):
        logger.error("Trade Drawer V2 Pine paste failed — aborting")
        return 6

    # 7. Favorite Trade Drawer V2
    if not favorite_indicator(browser, "Trade Drawer V2"):
        logger.warning("Favoriting Trade Drawer V2 failed — manual fix needed before tte-N runs")

    # 8. Save layout as "Snapshot"
    if not save_layout_as(browser, cfg.snapshot_layout):
        logger.error(f"Save layout '{cfg.snapshot_layout}' failed")
        return 7

    # 9. Open alerts sidebar (reuses existing setup_tv helper).
    if not browser.setup_tv():
        logger.warning("setup_tv post-pass returned False — verify alerts panel manually")

    logger.info("WS-D onboarding complete.")
    logger.info("Next step: deploy tte-N container with env_file pointing at this account.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Onboard a fresh TradingView account for TTE.")
    p.add_argument("--email", required=True, help="TV account email (for log clarity)")
    p.add_argument(
        "--user-data-suffix",
        default="-tte-2",
        help="Suffix for Chrome user-data-dir (matches Browser arg)",
    )
    p.add_argument("--instance", default="tte-2", help="Target TTE_INSTANCE identifier")
    p.add_argument(
        "--commit",
        action="store_true",
        help="Run for real (without this flag the script is a dry-run)",
    )
    args = p.parse_args(argv)

    cfg = OnboardConfig(
        email=args.email,
        user_data_suffix=args.user_data_suffix,
        instance=args.instance,
        dry_run=not args.commit,
    )
    return run_onboarding(cfg)


if __name__ == "__main__":
    sys.exit(main())
