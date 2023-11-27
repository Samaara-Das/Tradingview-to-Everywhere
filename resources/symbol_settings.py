
'''
This holds all the functions and variables related to the symbols. In total, there are 268 symbols.
'''
from .categories import *

# this is where all the symbols are stored
main_symbols = {
    CURRENCIES_WEBHOOK_NAME: ['GBPAUD', 'AUDJPY', 'EURCAD', 'EURGBP', 'USDCHF', 'AUDNZD', 'XAUUSD', 'WTIUSD', 'EURNZD', 'USDJPY', 'NZDJPY', 'GBPUSD', 'AUDCAD', 'EURJPY', 'GBPNZD', 'AUDCHF', 'GBPJPY', 'EURUSD', 'EURCHF', 'GBPCAD', 'AUDUSD', 'XAGUSD', 'NZDUSD', 'EURAUD', 'CADCHF', 'CHFJPY', 'GBPCHF', 'NZDCHF', 'CADJPY', 'USDCAD', 'NZDCAD'],

    US_STOCKS_WEBHOOK_NAME: ['UBER', 'LCID', 'KO', 'DIS', 'COIN', 'RIOT', 'SWN', 'NEE', 'C', 'MSFT', 'KMI', 'CDE', 'SOFI', 'AIC', 'IOVA', 'BAC', 'HBAN', 'F', 'OXY', 'VFS', 'KVUE', 'SQ', 'U', 'CHPT', 'XOM', 'META', 'WFC', 'AMD', 'LYFT', 'VZ', 'CMCSA', 'NEM', 'CCL', 'TSLA', 'M', 'FSR', 'KEY', 'DKNG', 'INTC', 'RIVN', 'T', 'SIRI', 'QCOM', 'HBI', 'RBLX', 'PYPL', 'OPEN', 'NVDA', 'MARA', 'KSS', 'PFE', 'NVAX', 'FCX', 'AMZN', 'NCLH', 'CLSK', 'CVX', 'AFRM', 'WBA', 'AMC', 'JWN', 'GPS', 'SPCE', 'PLUG', 'SNAP', 'HPE', 'GOOG', 'BMY', 'SHOT', 'AEO', 'GRAB', 'SHOP', 'CSCO', 'PCG', 'FUBO', 'RUN', 'MRO', 'NU', 'KHC', 'AAL', 'SOUN', 'AAPL', 'DDD', 'IRBT', 'SPRC', 'MU', 'DVN', 'HL', 'WMT', 'PLTR', 'GM', 'CSX', 'JBLU', 'CCAPT', 'WBD', 'RIG', 'HPQ', 'ET', 'DAL', 'HOOD'],

    INDIAN_STOCKS_WEBHOOK_NAME: ['ZOMATO', 'NTPC', 'GGMRP_UI', 'IDEA', 'COALINDIA', 'IRFC', 'SJVN', 'HCC', 'HINDCOPPER', 'PAYTM', 'KESORAMIND', 'GAIL', 'EEASEMYTRIP', 'DISHTV', 'JPASSOCIAT', 'PNB', 'ALOKINDS', 'EQUITASBNK', 'IIRB', 'PFC', 'TATAPOWER', 'AARSHIYA', 'IEX', 'GMRINFRA', 'BEL', 'YESBANK', 'SSEACOAST', 'IFCI', 'SOUTHBANK', 'MANINFRA', 'URJA', 'RAILTEL', 'SSBC', 'GRANULES', 'SSYNCOMF', 'ADANIPOWER', 'JSWENERGY', 'TATAMOTORS', 'KKBCGLOBAL', 'RTNINDIA', 'IOC', 'UNIONBANK', 'FFCSSOFT', 'JPPOWER', 'SBIN', 'EDELWEISS', 'MOREPENLAB', 'MMISHTANN', 'PPPLPHARMA', 'MUNJALAU', 'SAIL', 'HINDPETRO', 'GMDCLTD', 'VVIKASECO', 'SUZLON', 'ITC', 'MANAPPURAM', 'IDFCFIRSTB', 'GREENPOWER', 'VAKRANGEE', 'MRPL', 'JJIOFIN', 'GICRE', 'TV18BRDCST', 'VVIKASLIFE', 'SNOWMAN', 'HHONASA', 'HATHWAY', '3IINFOLTD', 'ASHOKLEY', 'BANDHANBNK', 'SPARC', 'RENUKA', 'INFIBEAM', 'SSEPC', 'NIACL', 'LICI', 'BHEL', 'NMDC', 'EESSENTIA', 'IRCON', 'ICICIBANK', 'NATIONALUM', 'IBREALEST', 'NBCC', 'NHPC', 'AXISBANK', 'MAHABANK', 'RVNL', 'POWERGRID', 'ZEEL', 'HDFCBANK', 'RTNPOWER', 'SEQUENT', 'AAKSHAR', 'BAJAJHIND', 'RECLTD', 'RPOWER', 'TATASTEEL', 'RBLBANK'],

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

def fill_symbol_set(symbol_inputs: int):
    '''This fills up `symbol_set`'s key-value pairs. It changes the values to lists with sublists. Each sublist has a maximum of `symbol_inputs` symbols.'''
    for category, symbols in main_symbols.items():
        sublists = [symbols[i:i+symbol_inputs] for i in range(0, len(symbols), symbol_inputs)]  # Split symbols into sublists of symbol_inputs
        if sublists and len(sublists[-1]) < symbol_inputs:  # If some symbols are remaining
            last_sublist = sublists.pop() if sublists else []  # Pop the last sublist if it exists
            sublists.append(last_sublist)  # Add the remaining symbols in a new sublist
        symbol_set[category] = sublists  # Fill up the symbol_set dictionary

def symbol_category(symbol):
    '''
    This function returns the symbol category. It retrieves the category of `symbol` (whether it is a US stock, forex pair, crypto pair, etc.)
    '''
    return symbol_categories.get(symbol, None)

      