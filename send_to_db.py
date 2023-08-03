'''
this is how we send post requests to Nishant uncle's database
'''

from requests import post

class Post:
  def __init__(self):
    self.url = 'https://pointcapitalis.com/meta/addTradeViewData'

  def post_to_url(self, payload: dict):
    post(self.url, data=payload)