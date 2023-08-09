'''
this has api keys & tokens for the twitter api. this has keys & tokens for 2 accounts: dassamaara & nili.thp.work.
this has a function which retrieves all the leys & tokens for the chosen account
'''


# these are for my own account
api_key = 'DsWRxt7H9H950Svfm8SCqr5GY'
api_secret = 'lJnfqE8ZI4ENSZe41jreSCyn8yvEvCYh5RuR4TUuBNRdzjLUAE'

bearer_token = r'AAAAAAAAAAAAAAAAAAAAAM%2F8oAEAAAAAezQvMrkkU1qqmyC615JRgw%2FLM2I%3DNwHrsACf5kW9s3WnaNJxb93omzLhlYqdenh83ego10uCD0D8Nw'

access_token = '1496761536953864194-LRDVHYzxm5kg03tbERvaT5BXiY3DvM'
access_token_secret = 'htr2XRRkMgqlemSpSLojzfIxhrOdCHgltN1DNd4dSaMlR'



# these are for the nili.thp.work account
api_key2 = '72G2uO5AyJfj8vhgDgnIsadip'
api_secret2 = 'hHn82IWQLrPCcFnH6YSDCdfVh0OlpYoZ1tURpJlp0Pn8a4mql5'

bearer_token2 = r'AAAAAAAAAAAAAAAAAAAAAELSowEAAAAAChjeG0wtdBUIhbLkrCPgsk3q9l0%3DC3QhfuxBS7131jpcaG5HUnezk4qyDVtQQs2oQb6Hdh1WFJWZi9'

access_token2 = '1682766611533672452-4OMVioLYlQMXIfr5p3uYC69SClnWeh'
access_token_secret2 = 'VkHrdU9FC6JheBo0LVDfKz4YiwbC1MgYVtQKiFSUVqmGe'


def get_tokens_of_account(user: int):
    if user == 1: #my account
        return (bearer_token, api_key, api_secret, access_token, access_token_secret)
    if user == 2: #nili.thp.work account
        return (bearer_token2, api_key2, api_secret2, access_token2, access_token_secret2)