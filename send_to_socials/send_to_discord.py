'''
Sends messages to discord webhooks.

if you have to create a webhook url, do this:
go to a discord channel -> Edit channel -> Integrations -> Webhooks -> New Webhook
'''
import logger_setup 
from discord_webhook import DiscordWebhook
from resources.categories import *

# Set up logger for this file
discord_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

class Discord:
    def __init__(self):
        self.entry_webhook_urls = {
            CURRENCIES_WEBHOOK_NAME: CURRENCIES_ENTRY_WEBHOOK_LINK,
            US_STOCKS_WEBHOOK_NAME: US_STOCKS_ENTRY_WEBHOOK_LINK,
            INDIAN_STOCKS_WEBHOOK_NAME: INDIAN_STOCKS_ENTRY_WEBHOOK_LINK,
            CRYPTO_WEBHOOK_NAME: CRYPTO_ENTRY_WEBHOOK_LINK,
            INDICES_WEBHOOK_NAME: INDICES_ENTRY_WEBHOOK_LINK
        }

        self.exit_webhook_urls = {
            CURRENCIES_WEBHOOK_NAME: CURRENCIES_EXIT_WEBHOOK_LINK,
            US_STOCKS_WEBHOOK_NAME: US_STOCKS_EXIT_WEBHOOK_LINK,
            INDIAN_STOCKS_WEBHOOK_NAME: INDIAN_STOCKS_EXIT_WEBHOOK_LINK,
            CRYPTO_WEBHOOK_NAME: CRYPTO_EXIT_WEBHOOK_LINK,
            INDICES_WEBHOOK_NAME: INDICES_EXIT_WEBHOOK_LINK
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
