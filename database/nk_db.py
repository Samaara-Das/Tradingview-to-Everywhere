'''
this is how we send post requests to Nishant uncle's database
'''

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError
from traceback import format_exc

class Post:
  def __init__(self, max_retries=3):
    self.url = 'https://pointcapitalis.com/meta/addTradeViewData'
    self.adapter = HTTPAdapter(max_retries=max_retries)
    self.session = Session()
    self.session.mount(self.url, self.adapter)

  def post_to_url(self, payload: dict):
    try:
      response = self.session.post(self.url, data=payload)
    except ConnectionError as e:
      print(f'from {__file__}: \nerror in sending post request to Nishant uncle\'s webhook: \n{e} ')
    else:
      return response
    

