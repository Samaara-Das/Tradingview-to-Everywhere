
'''
This has 1 main tuple. It holds different dictionaries.

Each dictionary has a ```type``` and ```symbols``` key. ```type``` is a string and ```symbols``` is a tuple of symbols.

Here's the count for each category of symbols:
CURRENCIES: 32 elements
US_STOCKS: 91 elements
INDIAN_STOCKS: 72 elements
CRYPTO: 18 elements
INDICES: 21 elements

In total, there's 234 symbols.

This module also has a function which returns the category of the passed in symbol.
'''
from .categories import *

main_symbols = (
    {'type': CURRENCIES, 'symbols': ("EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "EURAUD", "EURCHF", "AUDNZD", "NZDJPY", "GBPAUD", "GBPCAD", "EURNZD", "AUDCAD", "GBPCHF", "AUDCHF", "EURCAD", "CADJPY", "GBPNZD", "CADCHF", "CHFJPY", "NZDCAD", "NZDCHF", "XAUUSD", "XAGUSD", "WTIUSD")},

    {'type': US_STOCKS, 'symbols': ("NKE", "WBA", "DOW", "DIS", "INTC", "MSFT", "BA", "MMM", "AAPL", "KO", "CRM", "CSCO", "PG", "VZ", "HD", "GS", "AXP", "V", "JNJ", "AMGN", "MCD", "IBM", "CVX", "UNH", "CAT", "HON", "MRK", "WMT", "JPM", "TRV", "AAPL", "ABBV", "ABT", "ACN", "ADBE", "AIG", "AMD", "AMGN", "AMT", "AMZN", "AVGO", "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "BRK.B", "C", "CAT", "CHTR", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS", "CVX", "DE", "DHR", "DIS", "DOW", "DUK", "EMR", "EXC", "F", "FDX", "GD", "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON")},

    {'type': INDIAN_STOCKS, 'symbols': ("ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJFINSV", "BAJAJ_AUTO", "BAJFINANCE", "BHARTIARTL", "BPCL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "RELIANCE", "HDFCBANK", "ICICIBANK", "M_M", "TECHM", "INFY", "HDFC", "TCS", "KOTAKBANK", "ITC", "HINDUNILVR", "LT", "SBIN", "AXISBANK", "BAJFINANCE", "BHARTIARTL", "ASIANPAINT", "MARUTI", "HCLTECH", "TITAN", "SUNPHARMA", "BAJAJFINSV", "TATASTEEL", "ULTRACEMCO", "POWERGRID", "NTPC", "NESTLEIND", "TECHM", "WIPRO", "INDUSINDBK", "DRREDDY")},

    {'type': CRYPTO, 'symbols': ("ETHBTC", "ETHUSDT", "BTCUSDT", "LTCUSDT", "XRPUSDT", "LTCBTC", "XRPBTC", "BCHUSDT", "LINKUSDT", "BCHBTC", "DOGEUSDT", "TRXUSDT", "UNIUSDT", "TRXBTC", "EOSUSDT", "EOSBTC", "LINKBTC", "XLMUSDT", "NEOUSDT")},

    {'type': INDICES, 'symbols': ("DJI", "IXIC", "SPX", "RUT", "VIX", "FTSE", "GDAXI", "FCHI", "SENSEX", "NIFTY", "BANKNIFTY", "CNXMIDCAP", "SNSX50", "SMLCAP", "MIDCAP", "SMLSEL", "MIDSEL", "LRGCAP")}
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

