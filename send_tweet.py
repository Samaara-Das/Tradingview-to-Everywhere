'''
this file is for sending snapshots from tradingview to twitter
'''

import tweepy
from keys import *

class TwitterClient:
    def __init__(self):
        self.client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
        self.auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret) 
        self.api = tweepy.API(self.auth)

    def create_tweet(self, text):
        self.client.create_tweet(text=text)


