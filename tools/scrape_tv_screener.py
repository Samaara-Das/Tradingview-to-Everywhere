"""
Scrape a TradingView screener page into JSON rows for `ingest_scraped_symbols.py`.

Drives an isolated Selenium Chrome (NOT the tte-1 user-data-dir — must not
fight the running container for the session) against a public TV screener
URL. Scrolls to load all rows, extracts `symbol`, `companyName`, `exchange`,
`category` per row, writes JSON.

Usage:
    pipenv run python tools/scrape_tv_screener.py \\
        --url https://in.tradingview.com/screener/odIdLWwk/ \\
        --category 'US Stocks' \\
        --output scraped-us.json

    # Combine + ingest:
    pipenv run python tools/ingest_scraped_symbols.py scraped-us.json [--commit]

Notes:
- The screener URLs in the goal are SHAREABLE screener IDs:
    US: https://in.tradingview.com/screener/odIdLWwk/
    IN: https://in.tradingview.com/screener/LjEiKQHk/
  These render the screener with Sammy's saved filters/columns.
- The scraper does NOT log into TV. Public screener pages render enough rows
  to be useful, though TV may rate-limit unauthenticated bulk reads. If the
  row count looks short, pass --user-data-dir pointing at a logged-in profile.

Selector guesses (TV screener DOM, 2026 vintage):
    Row container:   tr[data-rowkey]
    Symbol cell:     td:nth-child(1) a (text = "EXCHANGE:SYMBOL" or just "SYMBOL")
    Description:     td:nth-child(2) (companyName)
    Exchange (often in symbol cell as prefix; we split)
These will likely need adjustment after the first dry run — TODO markers.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from tte import log

logger = log.setup_logger(__name__, log.INFO)

# Row + cell selectors. TODO: verify against the live screener; the screener
# DOM uses virtualized rendering so `tr` may not be the right primitive.
SEL_ROW = "tr[data-rowkey]"
SEL_SYMBOL_CELL = 'td[data-name="symbol"]'
SEL_SYMBOL_LINK = 'a[href*="/symbols/"]'
SEL_DESCRIPTION_CELL = 'td[data-name="description"]'

# Fallback: many TV screeners encode the row data in `data-*` attributes on
# the tr. If the cell-based scrape misses fields, the row-level fallback
# below attempts to read them.
ROW_DATA_SYMBOL_KEY = "data-rowkey"


def build_driver(user_data_dir: str | None, headless: bool) -> webdriver.Chrome:
    opts = Options()
    if user_data_dir:
        opts.add_argument(f"--user-data-dir={user_data_dir}")
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    chromedriver = os.environ.get("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")
    if not Path(chromedriver).exists():
        # Fall back to PATH; on Windows chromedriver is usually pip-installed.
        chromedriver = "chromedriver"
    return webdriver.Chrome(service=Service(chromedriver), options=opts)


def scroll_until_stable(driver, max_scrolls: int = 200, settle_seconds: float = 1.5) -> int:
    """Scroll the screener until the row count stops growing.

    TV virtualizes the table — rows render as you scroll. Returns the final
    row count detected.
    """
    last_count = 0
    stable_rounds = 0
    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(settle_seconds)
        # Some TV screeners use an inner scroll container; try both.
        driver.execute_script(
            "var c = document.querySelector('.table-container, [class*=\"scroll-\"]');"
            "if (c) c.scrollTop = c.scrollHeight;"
        )
        time.sleep(settle_seconds)
        count = len(driver.find_elements(By.CSS_SELECTOR, SEL_ROW))
        logger.info(f"  scroll #{i + 1}: {count} rows loaded")
        if count == last_count:
            stable_rounds += 1
            if stable_rounds >= 3:
                logger.info(f"Row count stable at {count} after {i + 1} scrolls")
                return count
        else:
            stable_rounds = 0
        last_count = count
    logger.warning(f"Hit max_scrolls={max_scrolls}; final row count {last_count}")
    return last_count


def extract_rows(driver, category: str) -> list[dict[str, Any]]:
    """Pull symbol / companyName / exchange from each visible row."""
    rows = driver.find_elements(By.CSS_SELECTOR, SEL_ROW)
    out: list[dict[str, Any]] = []
    for tr in rows:
        try:
            # Symbol — usually "NASDAQ:AAPL" or split into exchange prefix + ticker
            symbol_text = ""
            try:
                link = tr.find_element(By.CSS_SELECTOR, SEL_SYMBOL_LINK)
                symbol_text = (link.text or "").strip()
                if not symbol_text:
                    href = link.get_attribute("href") or ""
                    # /symbols/NASDAQ-AAPL/  →  NASDAQ:AAPL
                    if "/symbols/" in href:
                        slug = href.rstrip("/").split("/symbols/")[-1]
                        symbol_text = slug.replace("-", ":", 1)
            except Exception:
                pass

            if not symbol_text:
                # Fallback: data-rowkey attribute often holds the symbol
                symbol_text = (tr.get_attribute(ROW_DATA_SYMBOL_KEY) or "").strip()

            if not symbol_text:
                continue

            if ":" in symbol_text:
                exchange, ticker = symbol_text.split(":", 1)
                full_symbol = symbol_text
            else:
                exchange = ""
                ticker = symbol_text
                full_symbol = symbol_text  # caller may need to qualify later

            # Description / companyName
            company_name = ""
            try:
                desc = tr.find_element(By.CSS_SELECTOR, SEL_DESCRIPTION_CELL)
                company_name = (desc.text or "").strip()
            except Exception:
                pass

            out.append(
                {
                    "symbol": ticker,
                    "full_symbol": full_symbol,
                    "exchange": exchange,
                    "category": category,
                    "companyName": company_name,
                }
            )
        except Exception as e:
            logger.warning(f"Row extraction failed: {e}")
            continue

    # Dedupe by full_symbol (TV's virtualized rendering can repeat rows)
    seen: dict[str, dict[str, Any]] = {}
    for row in out:
        seen[row["full_symbol"]] = row
    return list(seen.values())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scrape a TradingView screener.")
    p.add_argument("--url", required=True, help="Screener URL")
    p.add_argument(
        "--category",
        required=True,
        choices=["US Stocks", "Indian Stocks", "Currencies", "Crypto"],
        help="Category tag for every row in this scrape",
    )
    p.add_argument("--output", required=True, type=Path, help="Output JSON path")
    p.add_argument(
        "--user-data-dir", default=None, help="Optional Chrome user-data-dir (logged-in profile)"
    )
    p.add_argument("--max-scrolls", type=int, default=200, help="Max scroll iterations")
    p.add_argument("--settle", type=float, default=1.5, help="Seconds between scrolls")
    p.add_argument(
        "--no-headless", action="store_true", help="Run with visible Chrome (for debugging)"
    )
    args = p.parse_args(argv)

    logger.info(f"Scraping {args.category}: {args.url}")
    driver = build_driver(args.user_data_dir, headless=not args.no_headless)
    try:
        driver.get(args.url)
        # Wait for initial paint
        time.sleep(5)
        scroll_until_stable(driver, args.max_scrolls, args.settle)
        rows = extract_rows(driver, args.category)
        logger.info(f"Extracted {len(rows)} unique rows for {args.category}")
        if not rows:
            logger.error("Zero rows extracted — selectors likely need adjustment")
            return 3

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        logger.info(f"Wrote {args.output}")
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
