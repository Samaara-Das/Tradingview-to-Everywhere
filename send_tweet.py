'''
this file is for sending snapshots from tradingview to twitter
'''

import tweepy
from keys import get_tokens_of_account


class TwitterClient:
    def __init__(self):
        bearer_token, api_key, api_secret, access_token, access_token_secret = get_tokens_of_account(2)
        self.client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
        self.auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret) 
        self.api = tweepy.API(self.auth, wait_on_rate_limit=True)

    def create_tweet(self, text):
        try:
            self.client.create_tweet(text=text)
        except Exception as e:
            print(f'from {__file__}: \n', e)


