# syntax=docker/dockerfile:1.7
# TTE — Linux container for headless Chrome + Selenium against TradingView.
# One container per TV Ultimate account; each gets its own user-data-dir volume.

FROM python:3.11-slim-bookworm

# System deps + Chrome stable. Use --batch --yes on gpg --dearmor so it never
# prompts for an overwrite confirmation in non-TTY builds (handoff bug #3).
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      curl unzip ca-certificates fonts-liberation \
      libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
      libdrm2 libgbm1 libxshmfence1 \
      gnupg; \
    install -d -m 0755 /etc/apt/keyrings; \
    rm -f /etc/apt/keyrings/google-chrome.gpg; \
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
      | gpg --batch --yes --dearmor -o /etc/apt/keyrings/google-chrome.gpg; \
    echo "deb [signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends google-chrome-stable; \
    \
    # ChromeDriver: don't construct the URL from chrome --product-version
    # (handoff bug #4). Query LATEST_RELEASE_<MAJOR> for the matching CfT build.
    CHROME_MAJOR=$(google-chrome --product-version | cut -d. -f1); \
    CHROMEDRIVER_VER=$(curl -fsSL "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR}"); \
    curl -fsSL "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VER}/linux64/chromedriver-linux64.zip" -o /tmp/cd.zip; \
    unzip -q /tmp/cd.zip -d /tmp; \
    install -m 0755 /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver; \
    \
    # Cleanup
    rm -rf /tmp/* /var/lib/apt/lists/* /etc/apt/sources.list.d/google-chrome.list

WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pip install --no-cache-dir pipenv \
 && pipenv install --system --deploy --ignore-pipfile

COPY . .

# Non-root runtime user. Each container's chrome-profile lives in /home/tte
# and is bind-mounted from a per-instance Docker volume (so isolation is by volume).
RUN useradd -m -u 1000 tte \
 && mkdir -p /home/tte/chrome-profile /app/logs \
 && chown -R tte:tte /home/tte /app

USER tte

ENV CHROME_USER_DATA_DIR=/home/tte/chrome-profile \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver \
    CHROME_PROFILES_PATH=/home/tte/chrome-profile \
    LOG_DIR=/app/logs \
    PYTHONUNBUFFERED=1

CMD ["python", "-m", "tte.main"]
