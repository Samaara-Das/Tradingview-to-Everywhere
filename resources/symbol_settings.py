
'''
this has 1 maoin tuple. it holds different dictionaries

each dictionary has a ```type``` and ```symbols``` key.
```type``` is a string and ```symbols``` is a tuple of symbols
'''

main_symbols = (
    { 'type': 'Currencies', 
    'symbols': ('EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURGBP', 'EURAUD', 'EURCAD', 'EURCHF', 'EURJPY', 'EURNZD', 'GBPEUR', 'GBPJPY', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPNZD', 'JPYAUD', 'JPYCAD', 'JPYCHF', 'JPYEUR', 'JPYGBP', 'JPYNZD', 'AUDCAD', 'AUDCHF', 'AUDEUR', 'AUDGBP', 'AUDJPY', 'AUDNZD', 'CADAUD', 'CADCHF', 'CADEUR', 'CADGBP', 'CADJPY', 'CADNZD', 'CHFAUD', 'CHFCAD', 'CHFEUR', 'CHFGBP', 'CHFJPY', 'CHFNZD', 'NZDAUD', 'NZDCAD', 'NZDCHF', 'NZDEUR', 'NZDJPY', 'NZDGBP')
    },

    { 'type': 'US Stocks', 
    'symbols': ('AAPL', 'MSFT', 'GOOG', 'AMZN', 'NVDA', 'META', 'BRK.A', 'TSLA', 'V', 'UNH', 'JPM', 'JNJ', 'WMT', 'LLY', 'XOM', 'MA', 'PG', 'AVGO', 'HD', 'ORCL', 'CVX', 'MRK', 'KO', 'ABBV', 'PEP', 'BAC', 'COST', 'ADBE', 'CSCO', 'TMO', 'MCD', 'CRM', 'ACN', 'PFE', 'NFLX', 'AMD', 'DHR', 'LIN', 'ABT', 'CMCSA', 'WFC', 'NKE', 'TMUS', 'DIS', 'UPS', 'TXN', 'PM', 'MS', 'INTC', 'BA', 'CAT', 'INTU', 'UNP', 'NEE', 'COP', 'VZ', 'QCOM', 'IBM', 'AMGN', 'LOW', 'DE', 'BX', 'HON', 'BMY', 'AMAT', 'RTX', 'GE', 'SPGI', 'AXP', 'SCHW', 'GS', 'SBUX', 'NOW', 'LMT', 'MDT', 'BKNG', 'ELV', 'SYK', 'ISRG', 'BLK', 'ADP', 'MDLZ', 'T', 'TJX', 'GILD', 'ADI', 'LRCX', 'CVS', 'MMC', 'UBER', 'ABNB', 'C', 'VRTX', 'ETN', 'CI', 'REGN', 'CB', 'ZTS', 'SLB', 'BDX')
    },

    { 'type': 'Indian Stocks',
    'symbols': ('RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'HINDUNILVR', 'INFY', 'ITC', 'SBIN', 'BHARTIARTL', 'AIRTELPP.E1', 'BAJFINANCE', 'LICI', 'LT', 'KOTAKBANK', 'ASIANPAINT', 'HCLTECH', 'AXISBANK', 'ADANIENT', 'MARUTI', 'SUNPHARMA', 'TITAN', 'BAJAJFINSV', 'DMART', 'ULTRACEMCO', 'TATAMOTORS', 'ONGC', 'NESTLEIND', 'WIPRO', 'NTPC', 'JSWSTEEL', 'M_M', 'POWERGRID', 'ADANIPORTS', 'ADANIGREEN', 'LTIM', 'TATASTEEL', 'COALINDIA', 'HDFCLIFE', 'SIEMENS', 'HINDZINC', 'PIDILITIND', 'BAJAJ_AUTO', 'IOC', 'SBILIFE', 'HAL', 'GRASIM', 'DLF', 'TECHM', 'BRITANNIA', 'INDUSINDBK', 'VBL', 'ADANIPOWER', 'GODREJCP', 'HINDALCO', 'DIVISLAB', 'DABUR', 'CIPLA', 'BANKBARODA', 'INDIGO', 'ABB', 'AMBUJACEM', 'BEL', 'DRREDDY', 'ADANITRANS', 'EICHERMOT', 'VEDL', 'CHOLAFIN', 'SHREECEM', 'ZOMATO', 'SBICARD', 'ICICIPRULI', 'BAJAJHLDNG', 'HAVELLS', 'BPCL', 'TATACONSUM', 'GAIL', 'MARICO', 'TATAPOWER', 'MCDOWELL_N', 'MANKIND', 'APOLLOHOSP', 'ATGL', 'PFC', 'IDBI', 'LODHA', 'SHRIRAMFIN', 'TORNTPHARM', 'POLYCAB', 'ICICIGI', 'BERGEPAINT', 'SRF', 'JINDALSTEL', 'MOTHERSON', 'PNB', 'ZYDUSLIFE', 'IRFC', 'TVSMOTOR', 'NAUKRI', 'CGPOWER', 'TRENT')
    },

    { 'type': 'Cyptocurrencies', 
    'symbols': ('BTCUSD', 'ETHUSD', 'USDTUSD', 'BNBUSD', 'XRPUSD', 'USDCUSD', 'DOGEUSD', 'ADAUSD', 'SOLUSD', 'TRXUSD', 'MATICUSD', 'LTCUSD', 'DOTUSD', 'SHIBUSD', 'DAIUSD', 'WBTCUSD', 'BCHUSD', 'AVAXUSD', 'TONUSD', 'XLMUSD', 'LINKUSD', 'LEOUSD', 'BUSDUSD', 'UNIUSD', 'TUSDUSD', 'ATOMUSD', 'XMRUSD', 'OKBUSD', 'ETCUSD', 'HBARUSD', 'FILUSD', 'ICPUSD', 'MNTUSD', 'LDOUSD', 'CROUSD', 'APTOUSD', 'ARBIUSD', 'VETUSD', 'NEARUSD', 'OPUSD', 'QNTUSD', 'MKRUSD', 'GRTUSD', 'XDCUSD', 'AAVEUSD', 'ALGOUSD', 'SANDUSD', 'AXSUSD', 'STXSUSD', 'EGLDUSD', 'IMXUSD', 'EOSUSD', 'XTZUSD', 'USDDUSD', 'THETAUSD', 'MANAUSD', 'BSVUSD', 'SNXUSD', 'APEUSD', 'INJUSD', 'FTMUSD', 'RNDRUSD', 'NEOUSD', 'FLOWUSD', 'KAVAUSD', 'XECUSD', 'CHZUSD', 'CFXUSD', 'KCSUSD', 'CRVUSD', 'GALAUSD', 'RPLUSD', 'USDPUSD', 'KLAYUSD', 'PAXGUSD', 'ZECUSD', 'XAUTUSD', 'MIOTAUSD', 'GMXUSD', 'FXSUSD', 'LUNCUSD', 'PEPEUSD', 'CSPRUSD', 'BTTUSD', 'HTUSD', 'COMPUSD', 'SUIUSD', 'MINAUSD', 'GTUSD', 'TWTUSD', 'DASHUSD', 'BONEUSD', 'GUSDUSD', 'NEXOUSD', 'ARUSD', 'CAKEUSD', 'RUNEUSD', 'ZILUSD', 'NFTUSD', 'DYDXUSD')
    }
)





def symbol_category(symbol):
    '''
    this function returns the symbol category. this returns the type of the symbol (whther it is a US stock, forex, crypto etc)
    '''

    for symbols in main_symbols:
        if symbol in symbols['symbols']:
            return symbols['type']
   
