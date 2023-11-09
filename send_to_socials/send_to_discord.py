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
            CURRENCIES: 'https://discord.com/api/webhooks/1167078736290652200/DISCORD_WEBHOOK_REMOVED',
            US_STOCKS: 'https://discord.com/api/webhooks/1167078636587851839/DISCORD_WEBHOOK_REMOVED',
            INDIAN_STOCKS: 'https://discord.com/api/webhooks/1167078313345421363/DISCORD_WEBHOOK_REMOVED',
            CRYPTO: 'https://discord.com/api/webhooks/1167078186509684736/DISCORD_WEBHOOK_REMOVED',
            INDICES: 'https://discord.com/api/webhooks/1167078015403040828/DISCORD_WEBHOOK_REMOVED',
        }

    def create_msg(self, category, content):
        try:
            webhook = DiscordWebhook(url=self.webhook_urls[category], content=content)
            response = webhook.execute()
        except Exception as e:
            print(f'error in {__file__}: \n{e}')

