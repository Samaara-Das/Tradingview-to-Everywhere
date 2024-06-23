'''
Sends messages to a Facebook group.
'''
import requests

access_token = 'EAAGIgRur2pcBO7KU9IQPR9x8IrQbZCrVM1ZBpQZABFQHMZAam4QC46dfl4rk9cuajNSOuYoIqH5njVYzdsSties8KDVKZAMFZCCZANIpVY9XU3dZBZCL3ktbk7H0F57N714nGSASVaBc3mkFrAvFflWRPd8YiXBvEDaW3nDrDc2StKa21RGDGptClKYkdw33FHPdIdJZAJAzM07aPm7I9ajFzD1j8ZD'

def post_to_md():
    '''This posts to the market davinci group'''
    group_id = 252647061266029

    msg = 'Take a look at this: https://www.tradingview.com/x/XrlZrnoc/'
    post_url = 'https://graph.facebook.com/{}/feed'.format(group_id)
    payload = {
    'message': msg,
    'access_token': access_token
    }

    r = requests.post(post_url, data=payload)
    print(r.text)

def get_user_info(user_id: int):
    '''Gets info about a user'''

    url = f'https://graph.facebook.com/{user_id}'
    params = {
        'access_token': access_token
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print(f'Error: {response.status_code}')
        print(response.text)

get_user_info(755604570)