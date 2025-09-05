import logger_setup 

# Set up logger for this file
x_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

from dotenv import load_dotenv
from os import getenv
import tweepy

load_dotenv('C:\\Users\\Puja\\Work\\Coding\\Python\\For Poolsifi\\tradingview to everywhere\\.env')

class TwitterClient:
    def __init__(self):
        bearer = getenv("X_BEARER")
        api_key = getenv("X_API_KEY")
        api_secret = getenv("X_API_SECRET")
        access_token = getenv("X_ACCESS_TOKEN")
        access_token_secret = getenv("X_ACCESS_SECRET")
        self.client = tweepy.Client(bearer, api_key, api_secret, access_token, access_token_secret)
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret) 
        api = tweepy.API(auth)

    def tweet(self, img: str, txt: str):
        '''
        Makes a tweet with the text and image.
        '''
        self.client.create_tweet(text=txt+'\n'+'Link: '+img)
