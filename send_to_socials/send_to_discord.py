'''
this file is for sending messages to discord

if you have to change the webhook url, do this:
go to a discord channel -> edit channel -> integrations -> create a webhook
'''

from discord_webhook import DiscordWebhook
from resources.categories import *

class Discord:
    def __init__(self):
        self.webhook_urls = {
            CURRENCIES: 'https://DISCORD_WEBHOOK_REVOKED',
            US_STOCKS: 'https://DISCORD_WEBHOOK_REVOKED',
            INDIAN_STOCKS: 'https://DISCORD_WEBHOOK_REVOKED',
            CRYPTO: 'https://DISCORD_WEBHOOK_REVOKED',
            INDICES: 'https://DISCORD_WEBHOOK_REVOKED',
        }

    def create_msg(self, category, content):
        try:
            webhook = DiscordWebhook(url=self.webhook_urls[category], content=content)
            response = webhook.execute()
        except Exception as e:
            print(f'error in {__file__}: \n{e}')

