'''
this file is for sending messages to discord

if you have to change the webhook url, do this:
go to a discord channel -> edit channel -> integrations -> create a webhook
'''
from traceback import print_exc
from discord_webhook import DiscordWebhook
from resources.categories import *

class Discord:
    def __init__(self):
        self.webhook_urls = {
            CURRENCIES_WEBHOOK_NAME: CURRENCIES_WEBHOOK_LINK,
            US_STOCKS_WEBHOOK_NAME: US_STOCKS_WEBHOOK_LINK,
            INDIAN_STOCKS_WEBHOOK_NAME: INDIAN_STOCKS_WEBHOOK_LINK,
            CRYPTO_WEBHOOK_NAME: CRYPTO_WEBHOOK_LINK,
            INDICES_WEBHOOK_NAME: INDICES_WEBHOOK_LINK
        }

    def create_msg(self, category, content):
        try:
            webhook = DiscordWebhook(url=self.webhook_urls[category], content=content)
            response = webhook.execute()
        except Exception as e:
            print_exc()

