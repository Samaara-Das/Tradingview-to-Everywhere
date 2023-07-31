'''
this file is for sending messages to discord

if you have to change the webhook url, do this:
go to a discord channel -> edit channel -> integrations -> create a webhook

then paste the webhook url in ``self.webhook_url``
'''

from discord_webhook import DiscordWebhook


class Discord:
    def __init__(self):
        self.webhook_url = 'https://discord.com/api/webhooks/1135604120481431786/iF9DIOWHPRgbtdKLF2RimUmztME_jUmt19lCoBRk9FIcApWYI3ciPLnVmR33XEUQ0aQx'

    def create_msg(self, content):
        try:
            webhook = DiscordWebhook(url=self.webhook_url, content=content)
            response = webhook.execute()
            print(response.reason)
        except Exception as e:
            print(e)

