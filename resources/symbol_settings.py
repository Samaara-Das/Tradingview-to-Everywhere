
'''
This holds all the functions and variables related to the symbols. In total, there are 178 symbols.
This performs calculations assuming that the Premium Screener has 15 inputs.
'''
from .categories import *

# this is where all the symbols are stored
main_symbols = {
    CURRENCIES_WEBHOOK_NAME: ['GBPAUD', 'AUDJPY', 'EURCAD', 'EURGBP', 'USDCHF', 'AUDNZD', 'XAUUSD', 'WTIUSD', 'EURNZD', 'USDJPY', 'NZDJPY', 'GBPUSD', 'AUDCAD', 'EURJPY', 'GBPNZD', 'AUDCHF', 'GBPJPY', 'EURUSD', 'EURCHF', 'GBPCAD', 'AUDUSD', 'XAGUSD', 'NZDUSD', 'EURAUD', 'CADCHF', 'CHFJPY', 'GBPCHF', 'NZDCHF', 'CADJPY', 'USDCAD', 'NZDCAD'],

    US_STOCKS_WEBHOOK_NAME: ['AMGN', 'UNH', 'ACN', 'JNJ', 'CVS', 'BA', 'GE', 'GOOGL', 'FDX', 'COST', 'EXC', 'HD', 'BKNG', 'JPM', 'BK', 'PG', 'AMT', 'GD', 'AAPL', 'HON', 'MSFT', 'GOOG', 'MCD', 'BLK', 'INTC', 'CVX', 'GILD', 'VZ', 'ABBV', 'TRV', 'MRK', 'CMCSA', 'BMY', 'CRM', 'CHTR', 'F', 'CL', 'DOW', 'IBM', 'WMT', 'DUK', 'AVGO', 'COP', 'COF', 'V', 'DE', 'BRK.B', 'AMD', 'NKE', 'KO', 'ABT', 'GS', 'DHR', 'EMR', 'CAT', 'WBA', 'C', 'CSCO', 'ADBE', 'AXP', 'BAC', 'AIG', 'AMZN', 'GM', 'MMM', 'DIS'],

    INDIAN_STOCKS_WEBHOOK_NAME: ['SUNPHARMA', 'ADANIENT', 'POWERGRID', 'SBIN', 'BPCL', 'EICHERMOT', 'HDFC', 'CIPLA', 'ULTRACEMCO', 'COALINDIA', 'TCS', 'LT', 'BAJAJFINSV', 'WIPRO', 'APOLLOHOSP', 'HDFCBANK', 'BRITANNIA', 'INDUSINDBK', 'KOTAKBANK', 'NESTLEIND', 'BHARTIARTL', 'TITAN', 'DIVISLAB', 'TECHM', 'INFY', 'ASIANPAINT', 'ITC', 'M_M', 'RELIANCE', 'TATASTEEL', 'GRASIM', 'NTPC', 'ADANIPORTS', 'ICICIBANK', 'HEROMOTOCO', 'HINDALCO', 'HCLTECH', 'DRREDDY', 'BAJAJ_AUTO', 'MARUTI', 'HINDUNILVR', 'HDFCLIFE', 'BAJFINANCE', 'AXISBANK'],

    CRYPTO_WEBHOOK_NAME: ['BTCUSDT', 'BCHBTC', 'DOGEUSDT', 'TRXBTC', 'UNIUSDT', 'LTCUSDT', 'LTCBTC', 'BCHUSDT', 'ETHUSDT', 'XRPUSDT', 'LINKBTC', 'XRPBTC', 'TRXUSDT', 'XLMUSDT', 'ETHBTC', 'NEOUSDT', 'EOSUSDT', 'EOSBTC', 'LINKUSDT'],

    INDICES_WEBHOOK_NAME: ['RUT', 'SNSX50', 'GDAXI', 'SENSEX', 'VIX', 'NIFTY', 'SMLCAP', 'MIDCAP', 'DJI', 'FCHI', 'SMLSEL', 'FTSE', 'BANKNIFTY', 'CNXMIDCAP', 'SPX', 'MIDSEL', 'IXIC', 'LRGCAP']
}

# this is the same as main_symbols except that each list will have sublists of 15 symbols. The remaining symbols will be in the last sublist
symbol_set = {
    CURRENCIES_WEBHOOK_NAME: [], 
    US_STOCKS_WEBHOOK_NAME: [], 
    INDIAN_STOCKS_WEBHOOK_NAME: [], 
    CRYPTO_WEBHOOK_NAME: [], 
    INDICES_WEBHOOK_NAME: []
}

# this is a dictionary whose keys are the symbols and their values are the categories
symbol_categories = {}
for category, symbols in main_symbols.items():
    symbol_categories.update({symbol: category for symbol in symbols})  # Map each symbol to its category in symbol_categories

def fill_symbol_set():
    '''This fills up `symbol_set`'s key-value pairs. It changes the values to lists with sublists. Each sublist has a maximum of 15 symbols.'''
    for category, symbols in main_symbols.items():
        sublists = [symbols[i:i+15] for i in range(0, len(symbols), 15)]  # Split symbols into sublists of 15
        if sublists and len(sublists[-1]) < 15:  # If some symbols are remaining
            last_sublist = sublists.pop() if sublists else []  # Pop the last sublist if it exists
            sublists.append(last_sublist)  # Add the remaining symbols in a new sublist
        symbol_set[category] = sublists  # Fill up the symbol_set dictionary

def symbol_category(symbol):
    '''
    This function returns the symbol category. It retrieves the category of `symbol` (whether it is a US stock, forex pair, crypto pair, etc.)
    '''
    return symbol_categories.get(symbol, None)

