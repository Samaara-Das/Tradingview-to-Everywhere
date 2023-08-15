
'''
this has 1 main tuple. it holds different dictionaries

each dictionary has a ```type``` and ```symbols``` key.
```type``` is a string and ```symbols``` is a tuple of symbols

this has a function which returns the category of the passed in symbol
'''

main_symbols = (
    { 'type': 'Currencies', 
    'symbols': ('EURUSD', 'GBPUSD', 'GBPJPY', 'USDJPY', 'AUDUSD', 'USDCAD', 'EURJPY', 'NZDUSD', 'USDCHF', 'AUDJPY', 'EURAUD', 'GBPAUD', 'AUDCAD', 'EURGBP', 'XAUUSD', 'USOIL')
    },

    { 'type': 'US Stocks', 
    'symbols': ('TSLA', 'AAPL', 'NVDA', 'AMZN', 'MSFT', 'AMD', 'META', 'PLTR', 'NFLX', 'GOOGL', 'COIN', 'DIS', 'PYPL', 'GOOG', 'RIVN', 'AMC', 'MARA', 'UPST', 'LCID', 'AI', 'SHOP', 'BA', 'SOFI', 'TLRY', 'LLY', 'CVNA', 'INTC', 'RIOT', 'SQ', 'ROKU', 'ABNB', 'SMCI', 'XOM', 'SNOW', 'DDOG', 'MSTR', 'DKNG', 'RBLX', 'TUP', 'BAC', 'JPM', 'ADBE', 'ENPH', 'GME', 'NKLA', 'UBER', 'NKE', 'PFE')
    },

    { 'type': 'Indian Stocks',
    'symbols': ('HDFCBANK', 'RELIANCE', 'SBIN', 'ICICIBANK', 'AXISBANK', 'TATAMOTORS', 'INFY', 'KOTAKBANK', 'TCS', 'ITC', 'BAJFINANCE', 'TECHM', 'WIPRO', 'ADANIENT', 'ADANIPORTS', 'DIXON', 'CIPLA', 'TATASTEEL', 'DRREDDY', 'HEROMOTOCO', 'M_M', 'INDUSINDBK', 'BIOCON', 'TATAPOWER', 'ASIANPAINT', 'HINDALCO', 'SBILIFE', 'TITAN', 'TATACHEM', 'VEDL', 'HINDUNILVR', 'HCLTECH')
    },

    { 'type': 'Crypto', 
    'symbols': ('BTCUSDT', 'BTCUSDT.P', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'DOGEUSDT', 'SHIBUSDT', 'MATICUSDT', 'ADAUSDT', 'ETHUSDT.P', 'OPUSDT', 'LINKUSDT', 'BTCUSD', 'BNBUSDT', 'LTCUSDT', 'SOLUSDT.P')
    },

    { 'type': 'Indices', 
    'symbols': ('DXY', 'SPX', 'VIX', 'US100', 'US30', 'DJI', 'NDQ', 'US500', 'NDX', 'IXIC')
    }
)




def symbol_category(symbol):
    '''
    this function returns the symbol category. this returns the category of ```symbol``` (whther it is a US stock, forex, crypto etc)
    '''

    for symbols in main_symbols:
        if symbol in symbols['symbols']:
            return symbols['type']
   
