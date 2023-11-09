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
            CURRENCIES: 'https://discord.com/api/webhooks/1167078736290652200/TUGdKcyEbubR2lL4EFu7fkDI47DbZ0oaUHeCTNbUtf6acUtuJVZr5ksx1FlWP4jpGjNF',
            US_STOCKS: 'https://discord.com/api/webhooks/1167078636587851839/BrRq8ExMkkcw8A4lnxoyZmLFnmCGoyhkjG9p62a4bcs3BsNP1Szx9v-jyPki63poTVIs',
            INDIAN_STOCKS: 'https://discord.com/api/webhooks/1167078313345421363/OsQ1-CFoygGk7rNA5fa5e-goMz_WzZOccTOl3Ko1_WC75pEonOi5MuWJ6hEx31uV9Mhg',
            CRYPTO: 'https://discord.com/api/webhooks/1167078186509684736/LrijSU5KExA06-agVhyoHwcd9fZsKlCMauCtJedlov6_QigiDcIga189x56PHQAX9u9G',
            INDICES: 'https://discord.com/api/webhooks/1167078015403040828/sQNU3ui0WmR2AucbjpgliKSFeBEvZyZkofWTh1EHW8GTMTtg4M_umaHLMVDoLQewJXwf',
        }

    def create_msg(self, category, content):
        try:
            webhook = DiscordWebhook(url=self.webhook_urls[category], content=content)
            response = webhook.execute()
        except Exception as e:
            print(f'error in {__file__}: \n{e}')

