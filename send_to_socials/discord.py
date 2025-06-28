"""
TradingView to Everywhere (TTE) - Discord Integration Module

Purpose: This module handles the distribution of trading signals and exit information to Discord channels
via webhook integration.

Functionality: This module provides Discord-specific distribution capabilities:
1. Sends trading entry signals to category-specific Discord channels
2. Sends trade exit notifications to category-specific Discord channels
3. Posts "before and after" comparisons showing entry and exit points
4. Manages webhook URLs for different categories (Currencies, US Stocks, Indian Stocks, Crypto)
5. Handles error logging for failed message deliveries

Dependencies:
- logger_setup.py: For application logging
- discord_webhook: For Discord webhook integration
- env.py: For environment variables containing webhook URLs and channel names

Usage: This module is primarily used by the handle_alerts.py and exits.py modules to send
formatted trade information to the appropriate Discord channels.

Note: To create a webhook URL, go to a Discord channel -> Edit channel -> Integrations ->
Webhooks -> New Webhook.
"""

import logger_setup 
from discord_webhook import DiscordWebhook
from env import *

# Set up logger for this file
discord_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

class Discord:
    def __init__(self):
        self.entry_webhook_urls = {
            CURRENCIES_WEBHOOK_NAME: CURRENCIES_ENTRY_WEBHOOK_LINK,
            US_STOCKS_WEBHOOK_NAME: US_STOCKS_ENTRY_WEBHOOK_LINK,
            INDIAN_STOCKS_WEBHOOK_NAME: INDIAN_STOCKS_ENTRY_WEBHOOK_LINK,
            CRYPTO_WEBHOOK_NAME: CRYPTO_ENTRY_WEBHOOK_LINK
        }

        self.exit_webhook_urls = {
            CURRENCIES_WEBHOOK_NAME: CURRENCIES_EXIT_WEBHOOK_LINK,
            US_STOCKS_WEBHOOK_NAME: US_STOCKS_EXIT_WEBHOOK_LINK,
            INDIAN_STOCKS_WEBHOOK_NAME: INDIAN_STOCKS_EXIT_WEBHOOK_LINK,
            CRYPTO_WEBHOOK_NAME: CRYPTO_EXIT_WEBHOOK_LINK
        }

        self.before_after_webhook_urls = {
            CURRENCIES_WEBHOOK_NAME: CURRENCIES_BEFORE_AFTER_WEBHOOK_LINK,
            US_STOCKS_WEBHOOK_NAME: US_STOCKS_BEFORE_AFTER_WEBHOOK_LINK,
            INDIAN_STOCKS_WEBHOOK_NAME: INDIAN_STOCKS_BEFORE_AFTER_WEBHOOK_LINK,
            CRYPTO_WEBHOOK_NAME: CRYPTO_BEFORE_AFTER_WEBHOOK_LINK
        }

    def send_to_entry_channel(self, category, content):
        try:
            webhook = DiscordWebhook(url=self.entry_webhook_urls[category], content=content)
            response = webhook.execute()
        except Exception as e:
            discord_logger.exception(f'Error sending "{content}" to {category} webhook for the entry channel. Response: {response} Error:')

    def send_to_exit_channel(self, category, content):
        try:
            webhook = DiscordWebhook(url=self.exit_webhook_urls[category], content=content)
            response = webhook.execute()
        except Exception as e:
            discord_logger.exception(f'Error sending "{content}" to {category} webhook for the exit channel. Response: {response} Error:')

    def send_to_before_and_after_channel(self, category, entry_img, exit_img):
        try:
            content = f"1st image -> entry: {entry_img} \n2nd image -> exit: {exit_img}"
            webhook = DiscordWebhook(url=self.before_after_webhook_urls[category], content=content)
            response = webhook.execute()
        except Exception as e:
            discord_logger.exception(f"Error sending \"{content}\" to {category} webhook for the exit channel. Response: {response} Error:", exc_info=e)
