import requests

# Starting June 2022, LinkedIn Marketing APIs will be versioned and released under the base path: https://api.linkedin.com/rest/. Each version will be supported for 12 months. When making API calls make sure to specify the version you want and include the request header with key “LinkedIn-Version” and date (YYYYMM).

CLIENT_ID = '86fzrened0vc97'
CLIENT_SECRET = 'WoQpbhIl6EwFkTBU'
ACCESS_TOKEN = 'AQWLs1DxYTaJeas5z1IkGVJsjwsqILZQir-Dlc6aNed6MC7ypV5x37hT7Te1-lKv5annWHSR0d-1CHUnUzsHGFVj6Q_s_3yXpf7w8zJjQOCWN-rKDno9yCs0A4USdleMyn85UgKFLQ3YhpLN97u87fXQ-E9VJGAqkazWnXwLsn8E1i0Vq47zOsL8fWDUosO8f4bqFJTgcqnVXtFY_rL-EoG6NJYMrDW3l5R9Z4wrKx8pZ4fX_eXrGHoeBYRobLEcQFYHYsJCeRHL5kOMWGc9zVe2W_cGXcEFiBmzvqLCUcCPJiCTvWJihnYqTJ5ogXToD5GjD28kK04gmLJNpRz-uagA7-fcjA'
PERSON_AUTHOR_ID = 'OJ7zXgqJEl'
ORG_AUTHOR_ID = '99288912' # the number in in the Market DaVinci LinkedIn URL
PERSON_AUTHOR_TYPE = 'person' 
ORG_AUTHOR_TYPE = 'organization' 
ORGANIZATION_URN = f'urn:li:{ORG_AUTHOR_TYPE}:{ORG_AUTHOR_ID}'
AD_ACCOUNT_ID = '695134886'

def get_user_info(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    return requests.get('https://api.linkedin.com/v2/userinfo', headers=headers)

def post_article():
    headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
    'LinkedIn-Version': '202406',
    'X-Restli-Protocol-Version': '2.0.0'
    }

    payload = {
    "author": f"urn:li:{PERSON_AUTHOR_TYPE}:{PERSON_AUTHOR_ID}",
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": 'Hi'
            },
            "shareMediaCategory": "ARTICLE",
            "media": [
                {
                    "status": "READY",
                    "originalUrl": "https://cloudnativeengineer.substack.com/p/how-to-publish-a-post-with-the-linkedin"
                }
            ]
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
    }

    response = requests.post('https://api.linkedin.com/v2/ugcPosts', headers=headers, json=payload)
    post_info = response.json()
    print(post_info)



def post_to_group():
    headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
    }
     
    payload = {
    "author":f'urn:li:person:{PERSON_AUTHOR_ID}',
    "containerEntity": "urn:li:group:2877", 
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": "Wonderful article as always by Ashu Garg."
            },
            "shareMediaCategory": "ARTICLE",
            "media": [
                {
                    "status": "READY",
                    "originalUrl": "https://ashugarg.substack.com/p/graduating-from-series-a-how-to-get",
                    "title": {
                        "text": "$100 million ARR"
                    }
                }
            ]
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "CONTAINER"
    }
    }
    
    response = requests.post('https://api.linkedin.com/v2/ugcPosts', headers=headers, json=payload)
    post_info = response.json()
    print(post_info)

def get_ad_acc_user():
    headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'LinkedIn-Version': '202406',
    'X-Restli-Protocol-Version': '2.0.0'
    }
    
    response = requests.get(f'https://api.linkedin.com/rest/adAccountUsers?q={ACCESS_TOKEN}', headers=headers)
    post_info = response.json()
    print(post_info)
# get_ad_acc_user() # {'status': 500, 'code': 'GATEWAY_INTERNAL_ERROR', 'message': 'INTERNAL_SERVER_ERROR'

def fetch_ad_acc():
    headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'LinkedIn-Version': '202406',
    'X-Restli-Protocol-Version': '2.0.0'
    }
    
    response = requests.get(f'https://api.linkedin.com/rest/adAccounts/{AD_ACCOUNT_ID}', headers=headers)
    post_info = response.json()
    print(post_info)
# fetch_ad_acc() # {'status': 403, 'serviceErrorCode': 100, 'code': 'ACCESS_DENIED', 'message': 'Not enough permissions to access: partnerApiAdAccounts.GET.20240601'}

def init_img_upload():
    headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'LinkedIn-Version': '202406',
    'X-Restli-Protocol-Version': '2.0.0'
    }

    payload = {
        "initializeUploadRequest": {
        "owner": ORGANIZATION_URN
        }
    }

    response = requests.post(f'https://api.linkedin.com/rest/images?action=initializeUpload', headers=headers)
    return response.json()

# print(init_img_upload()) # error 500