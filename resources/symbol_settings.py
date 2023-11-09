
'''
this has 1 main tuple. it holds different dictionaries

each dictionary has a ```type``` and ```symbols``` key.
```type``` is a string and ```symbols``` is a tuple of symbols

this has a function which returns the category of the passed in symbol
'''
from .categories import *

main_symbols = (
    { 'type': CURRENCIES, 
    'symbols': ('EURUSD', 'GBPUSD', 'GBPJPY', 'USDJPY', 'AUDUSD', 'USDCAD', 'EURJPY', 'NZDUSD', 'USDCHF', 'AUDJPY', 'EURAUD', 'GBPAUD', 'AUDCAD', 'EURGBP', 'XAUUSD', 'USOIL')
    },

    { 'type': US_STOCKS, 
    'symbols': ('TSLA', 'AAPL', 'NVDA', 'AMZN', 'MSFT', 'AMD', 'META', 'PLTR', 'NFLX', 'GOOGL', 'COIN', 'DIS', 'PYPL', 'GOOG', 'RIVN', 'AMC', 'MARA', 'UPST', 'LCID', 'AI', 'SHOP', 'BA', 'SOFI', 'TLRY', 'LLY', 'CVNA', 'INTC', 'RIOT', 'SQ', 'ROKU', 'ABNB', 'SMCI', 'XOM', 'SNOW', 'DDOG', 'MSTR', 'DKNG', 'RBLX', 'TUP', 'BAC', 'JPM', 'ADBE', 'ENPH', 'GME', 'NKLA', 'UBER', 'NKE', 'PFE')
    },

    { 'type': INDIAN_STOCKS,
    'symbols': ('HDFCBANK', 'RELIANCE', 'SBIN', 'ICICIBANK', 'AXISBANK', 'TATAMOTORS', 'INFY', 'KOTAKBANK', 'TCS', 'ITC', 'BAJFINANCE', 'TECHM', 'WIPRO', 'ADANIENT', 'ADANIPORTS', 'DIXON', 'CIPLA', 'TATASTEEL', 'DRREDDY', 'HEROMOTOCO', 'M_M', 'INDUSINDBK', 'BIOCON', 'TATAPOWER', 'ASIANPAINT', 'HINDALCO', 'SBILIFE', 'TITAN', 'TATACHEM', 'VEDL', 'HINDUNILVR', 'HCLTECH')
    },

    { 'type': CRYPTO, 
    'symbols': ('BTCUSDT', 'BTCUSDT.P', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'DOGEUSDT', 'SHIBUSDT', 'MATICUSDT', 'ADAUSDT', 'ETHUSDT.P', 'OPUSDT', 'LINKUSDT', 'BTCUSD', 'BNBUSDT', 'LTCUSDT', 'SOLUSDT.P')
    },

    { 'type': INDICES, 
    'symbols': ('DXY', 'SPX', 'VIX', 'US100', 'US30', 'DJI', 'NDQ', 'US500', 'NDX', 'IXIC')
    }
)

symbol_categories = {}

for category in main_symbols:
    for symbol in category['symbols']:
        symbol_categories[symbol] = category['type']

def symbol_category(symbol):
    '''
    This function returns the symbol category. It retrieves the category of `symbol` (whether it is a US stock, forex pair, crypto pair, etc.) quickly.
    '''
    return symbol_categories.get(symbol, None)

