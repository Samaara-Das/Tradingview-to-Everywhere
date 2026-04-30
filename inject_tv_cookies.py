"""
One-off bootstrap: inject TradingView session cookies into the Chrome profile
volume so TTE skips the (failing) automated sign-in flow.

Reads TV_SESSION_ID and TV_SESSION_ID_SIGN from env, writes them to the same
chrome user-data-dir that tte-1 will mount, then exits. After this runs once,
restart tte-1 normally — TV will recognize the existing session.

Usage (one-shot, from /opt/stockbuddy):
  docker compose run --rm \
    -e TV_SESSION_ID=... \
    -e TV_SESSION_ID_SIGN=... \
    --entrypoint python tte-1 inject_tv_cookies.py
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def main() -> int:
    user_data_dir = os.environ.get("CHROME_USER_DATA_DIR", "/home/tte/chrome-profile")
    sessionid = os.environ.get("TV_SESSION_ID")
    sessionid_sign = os.environ.get("TV_SESSION_ID_SIGN")
    if not sessionid or not sessionid_sign:
        print("ERROR: TV_SESSION_ID and TV_SESSION_ID_SIGN env vars are required")
        return 2

    opts = Options()
    opts.add_argument(f"--user-data-dir={user_data_dir}")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")

    print(f"Starting Chrome with user-data-dir={user_data_dir}…")
    driver = webdriver.Chrome(
        service=Service(os.environ.get("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")),
        options=opts,
    )

    try:
        # Visit the domain first so add_cookie can attach to it.
        driver.get("https://www.tradingview.com/")
        time.sleep(2)

        # Clear any existing TV cookies so we don't conflict with stale ones.
        driver.delete_cookie("sessionid")
        driver.delete_cookie("sessionid_sign")

        for name, value in (("sessionid", sessionid), ("sessionid_sign", sessionid_sign)):
            driver.add_cookie(
                {
                    "name": name,
                    "value": value,
                    "domain": ".tradingview.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                }
            )
            print(f"  injected cookie: {name}")

        # Force a reload so Chrome persists the cookie jar to disk.
        driver.get("https://www.tradingview.com/chart/")
        time.sleep(4)
        print(f"After chart visit — URL: {driver.current_url}")
        print(f"Title: {driver.title}")

        # Visit a definitely-authed page to confirm.
        driver.get("https://www.tradingview.com/u/")
        time.sleep(3)
        print(f"After /u/ visit — URL: {driver.current_url}")

        return 0
    finally:
        driver.quit()
        print("Done. Cookies persisted to user-data-dir.")


if __name__ == "__main__":
    raise SystemExit(main())
