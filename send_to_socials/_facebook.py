'''
Sends messages to a Facebook group.
'''
import facebook as fb
import requests
from io import BytesIO
import logger_setup 

# Set up logger for this file
fb_logger = logger_setup.setup_logger(__name__, logger_setup.INFO)

MD_APP_ID = '431563073116823' # app id for tte app on the Daniel Das account
MD_APP_SECRET = "abb9f1bd261780b27b5c109a38ba5b23" # app secret for tte app on the Daniel Das account
MD_PAGE_ACCESS_TOKEN = "EAAGIgRur2pcBOZBQ3tSLfxnwJoiSPbP9TzRwZBbfZC3Htt2ehEAWt5wew4UPmareLhRSbSbCMA1nJ9tKgCzz3rp8DCvZBTwDGevQRiJ2ZAsU2b2Nj2ejxkEXbZCLZB2xwqRNIQM0ZBK97BxVYcB9iYEZALksXWIqaRn7ZAZAPc5KZBdahsXs22v7ecWyqswDX67gpDcZD" # Access token for the Market Davinci page
MD_USER_ACCESS_TOKEN = "EAAGIgRur2pcBO5rZCVxc3Di6ZCs7ox0jZBUjLd77RFloB24ZBkstC0F14YTQeZCZAdFEPU7HcPxu0IEPybxtiuVNllXtSFJezu7XJctUnK0sq2OkcQOF7tZAPpN4jLOPsWB7yPzbJyoy7HZCb32ZCxEehUB5BIW5EyfRZBZBYwr0oihuLC14K69AT1oRVe5" # Access token for the Daniel Das account
MD_PAGE_ID = '252647061266029' # The ID of the Market Davinci Facebook page. To get this id, go to a Facebook page -> About -> Page transparency

graph = fb.GraphAPI(MD_PAGE_ACCESS_TOKEN)

def check_token_permissions(token: str) -> None:
    url = f"https://graph.facebook.com/debug_token"
    payload = {
        'input_token': token,
        'access_token': token
    }
    response = requests.get(url, params=payload)
    if response.status_code == 200:
        fb_logger.info("Token is valid.")
        fb_logger.info("Response:", response.json())
    else:
        fb_logger.error("Failed to check token.")
        fb_logger.error("Response:", response.json())

def download_image(img_url: str) -> BytesIO:
    '''
    Downloads an image from a URL and returns it as a BytesIO object.
    
    :param img_url: URL of the image to download
    :return: BytesIO object containing the image data
    '''
    try:
        response = requests.get(img_url, allow_redirects=True)
        if response.status_code == 200 and 'image' in response.headers['Content-Type']:
            return BytesIO(response.content)
        else:
            fb_logger.error(f"Failed to download image: Status code {response.status_code}, Content-Type {response.headers['Content-Type']}")
            return None
    except Exception as e:
        fb_logger.error(f"An error occurred while downloading the image: {e}")
        return None

def post(img_url: str, text: str = ""):
    '''
    Downloads an image from a URL and posts it with text to the Facebook page.
    
    :param img_url: URL of the image to post
    :param text: Text to accompany the image post
    '''
    try:
        # Download the image
        image = download_image(img_url)
        if image is None:
            fb_logger.error("Image URL is None")
            return

        # Post the image to Facebook
        result = graph.put_photo(image, message=text)
        
        # Log the result
        fb_logger.info(f"Posted to Facebook: {result}")
    
    except fb.GraphAPIError as e:
        fb_logger.error(f"Facebook GraphAPIError: {e}")
    except Exception as e:
        fb_logger.error(f"An error occurred: {e}")

def post_before_after(entry_img: str, exit_img: str, entry_txt: str, exit_txt: str):
    '''
    This posts 2 posts. One for an entry and one for an exit.
    '''
    post(entry_img, entry_txt)
    post(exit_img, exit_txt)

