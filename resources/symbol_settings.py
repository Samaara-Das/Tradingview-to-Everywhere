"""
This holds all the functions and variables related to the symbols.

Currencies - 30
US Stocks - 719
Indian Stocks - 268
Crypto - 19
Indices - 18
"""

import logger_setup 
from env import *

# Set up logger for this file
symbol_logger = logger_setup.setup_logger(__name__, logger_setup.DEBUG)

# this is where all the symbols are stored for every category
main_symbols = {
    CURRENCIES_WEBHOOK_NAME: ['GBPAUD', 'AUDJPY', 'EURCAD', 'EURGBP', 'USDCHF', 'AUDNZD', 'XAUUSD', 'EURNZD', 'USDJPY', 'NZDJPY', 'GBPUSD', 'AUDCAD', 'EURJPY', 'GBPNZD', 'GBPJPY', 'EURUSD', 'EURCHF', 'GBPCAD', 'AUDUSD', 'XAGUSD', 'NZDUSD', 'EURAUD', 'CADCHF', 'CHFJPY', 'GBPCHF', 'NZDCHF', 'CADJPY', 'USDCAD', 'NZDCAD'],

    CRYPTO_WEBHOOK_NAME: ['BTCUSDT', 'BCHBTC', 'DOGEUSDT', 'TRXBTC', 'UNIUSDT', 'LTCUSDT', 'LTCBTC', 'BCHUSDT', 'ETHUSDT', 'XRPUSDT', 'LINKBTC', 'XRPBTC', 'TRXUSDT', 'XLMUSDT', 'ETHBTC', 'NEOUSDT', 'EOSUSDT', 'EOSBTC', 'LINKUSDT'],

    INDIAN_STOCKS_WEBHOOK_NAME: ['DEVYANI', 'MMTC', 'PRAJIND', 'PTC', 'JUBLFOOD', 'NIACL', 'SIEMENS', 'TVTODAY', 'TRENT', 'M_M', 'BAYERCROP', 'ZENSARTECH', 'MAHABANK', 'MAHSEAMLES', 'ABCAPITAL', 'PRESTIGE', 'BAJAJFINSV', 'SCHNEIDER', 'RELIANCE', 'MASTEK', 'VENKEYS', 'PVR', 'CHOLAFIN', 'SYMPHONY', 'QUESS', 'COLPAL', 'ACC', 'MUTHOOTFIN', 'NFL', 'PETRONET', 'KEC', 'VAKRANGEE', 'SCI', 'CYIENT', 'PGHH', 'UPL', 'THYROCARE', 'SIS', 'SUNPHARMA', 'MRF', 'FCSSOFT', 'SONATSOFTW', 'COFORGE', 'MARUTI', 'JUBLINDS', 'SJVN', 'CRISIL', 'DABUR', 'ITC', 'MOTHERSON', 'BALKRISIND', 'COALINDIA', 'LTI', 'PAGEIND', 'RBLBANK', 'LICHSGFIN', 'MGL', 'AJANTPHARM', 'TATASTEEL', 'NESTLEIND', 'EQUITASBNK', 'BRITANNIA', 'UNIONBANK', 'KAJARIACER', 'VIKASECO', 'AIAENG', 'KPRMILL', 'SBILIFE', 'APARINDS', 'ESSENTIA', 'SUNTV', 'RAMCOCEM', 'ASHOKLEY', 'RCF', 'GRANULES', 'CANBK', 'TITAN', 'MIDHANI', 'BLUESTARCO', 'KANSAINER', 'MCX', 'HCC', 'APOLLOTYRE', 'TEXRAIL', 'PRSMJOHNSN', 'JINDALSTEL', 'BANKINDIA', 'BERGEPAINT', 'BAJFINANCE', 'HINDPETRO', 'NCC', 'JKCEMENT', 'KOTAKBANK', 'THERMAX', 'AMBUJACEM', 'MOIL', 'JPASSOCIAT', 'PFC', 'SANOFI', 'AUROPHARMA', 'UCOBANK', 'IFCI', 'RALLIS', 'HATHWAY', 'TV18BRDCST', 'KPITTECH', 'MARICO', 'BEL', 'ABBOTINDIA', 'CREDITACC', 'PERSISTENT', 'TATACOFFEE', 'DMART', 'PNB', 'WHIRLPOOL', 'WELCORP', 'IOC', 'NAUKRI', 'KSCL', 'UJJIVAN', 'MANAPPURAM', 'BANKBARODA', 'POLYCAB', 'APOLLOHOSP', 'JSWENERGY', 'INDUSINDBK', 'LUPIN', 'VEDL', 'JKLAKSHMI', 'JPPOWER', 'STAR', 'KRBL', 'BHARTIARTL', 'TATAPOWER', 'ABFRL', 'WESTLIFE', 'CARBORUNIV', 'PFIZER', 'NETWORK18', 'TATACOMM', 'IIFL', 'ICICIBANK', 'ADANIENT', 'ABB', 'VIPIND', 'SKFINDIA', 'TVSMOTOR', 'WOCKPHARMA', 'INFIBEAM', 'SBICARD', 'ADANIENSOL', 'BOSCHLTD', 'JUSTDIAL', 'MAHINDCIE', 'HDFCBANK', 'BHEL', 'GICRE', 'AUBANK', 'LALPATHLAB', 'BPCL', 'TATAMOTORS', 'WIPRO', 'HONASA', 'JMFINANCIL', 'SOLARINDS', 'ANGELONE', 'RECLTD', 'CIPLA', 'BATAINDIA', 'GODFRYPHLP', 'IRB', 'APLAPOLLO', 'ASTRAL', 'DEEPAKNTR', 'SUPRAJIT', 'BANDHANBNK', 'YESBANK', 'TECHM', 'ADANIPOWER', 'KARURVYSYA', 'ORIENTCEM', 'TATAMTRDVR', 'MPHASIS', 'TORNTPHARM', 'ZEEL', 'BHARATFORG', 'COROMANDEL', 'KTKBANK', 'ULTRACEMCO', 'NBCC', '3MINDIA', 'CUMMINSIND', 'TEAMLEASE', 'BIOCON', 'SOUTHBANK', 'AXISBANK', 'SCHAEFFLER', 'LT', 'JSWSTEEL', 'DLF', 'GM', 'SWANENERGY', 'UBL', 'MFSL', 'SPARC', 'TATAELXSI', 'BAJAJ_AUTO', 'NRBBEARING', 'RELCAPITAL', 'SYNGENE', 'LTTS', 'WELSPUNLIV', 'ONGC', 'UFLEX', 'IRCON', 'ATGL', 'VSTIND', 'TORNTPOWER', 'SUZLON', 'ADANIPORTS', 'CENTRALBK', 'INDIGO', 'NTPC', 'VRLLOG', 'DIVISLAB', 'SHREECEM', 'ASIANPAINT', 'VBL', 'RATNAMANI', 'SAIL', 'AIRTELPP', 'DALBHARAT', 'NBVENTURES', 'DIXON', 'VAIBHAVGBL', 'IDFCFIRSTB', 'PIDILITIND', 'NATIONALUM', 'GAIL', 'DELHIVERY', 'VGUARD', 'BDL', 'LINDEINDIA', 'CONCOR', 'MHRIL', 'NOCIL', 'NHPC', 'AWL', 'ALKEM', 'SMLISUZU', 'PIIND', 'ZYDUSWELL', 'CGPOWER', 'GMDCLTD', 'TVVISION', 'POWERGRID', 'TATACHEM', 'TRIDENT', 'TIMKEN', 'ADANIGREEN', 'BAJAJHLDNG', 'TATAINVEST', 'BSE', 'OBEROIRLTY', 'IBREALEST', 'MRPL'],

    US_STOCKS_WEBHOOK_NAME: ['MSFT', 'NVDA', 'AAPL', 'AMZN', 'GOOG', 'META', 'BRK.A', 'TSLA', 'AVGO', 'WMT', 'JPM', 'LLY', 'V', 'MA', 'NFLX', 'COST', 'XOM', 'ORCL', 'PG', 'HD', 'JNJ', 'BAC', 'ABBV', 'KO', 'PLTR', 'BABA', 'UNH', 'TMUS', 'CRM', 'PM', 'CSCO', 'GE', 'IBM', 'WFC', 'CVX', 'ABT', 'MCD', 'LIN', 'NOW', 'MS', 'AXP', 'DIS', 'T', 'ISRG', 'ACN', 'MRK', 'UBER', 'GS', 'INTU', 'VZ', 'AMD', 'RTX', 'PEP', 'ADBE', 'BX', 'BKNG', 'TXN', 'PGR', 'QCOM', 'CAT', 'PDD', 'SCHW', 'SPGI', 'BSX', 'TMO', 'BA', 'BLK', 'NEE', 'SYK', 'TJX', 'AMGN', 'HON', 'DE', 'C', 'SHOP', 'DHR', 'ARM', 'UNP', 'AMAT', 'SPOT', 'CMCSA', 'GILD', 'LOW', 'ADP', 'PFE', 'MELI', 'ETN', 'PANW', 'COF', 'APP', 'GEV', 'ANET', 'CB', 'CHTR', 'MMC', 'COP', 'VRTX', 'MSTR', 'KKR', 'MDT', 'ADI', 'LMT', 'CRWD', 'MU', 'LRCX', 'PLD', 'APH', 'KLAC', 'ICE', 'AMT', 'MO', 'CME', 'WELL', 'SO', 'BN', 'SE', 'SBUX', 'BMY', 'TT', 'BAM', 'FI', 'WM', 'INTC', 'HCA', 'CEG', 'NKE', 'ELV', 'DUK', 'MCK', 'SHW', 'CTAS', 'VTR', 'MCO', 'AJG', 'IBKR', 'CDNS', 'PH', 'CI', 'EQIX', 'DASH', 'ABNB', 'MDLZ', 'UPS', 'MMM', 'APO', 'TDG', 'FTNT', 'SNPS', 'DELL', 'ORLY', 'CVS', 'AON', 'RSG', 'GD', 'MAR', 'NTES', 'CL', 'ECL', 'ITW', 'SCCO', 'WDAY', 'ZTS', 'WMB', 'MSI', 'PNC', 'EPD', 'CMG', 'PYPL', 'USB', 'RCL', 'NOC', 'EMR', 'COIN', 'HWM', 'CRH', 'CVNA', 'CARR', 'AZO', 'BK', 'REGN', 'JCI', 'ADSK', 'NU', 'ROP', 'KMI', 'TRV', 'EOG', 'ET', 'APD', 'MNST', 'CPRT', 'HLT', 'SNOW', 'CSX', 'AXON', 'AFL', 'DLR', 'PAYX', 'COR', 'HOOD', 'NEM', 'TEAM', 'FCX', 'ALL', 'AEP', 'RBLX', 'NSC', 'NET', 'PSA', 'MET', 'TFC', 'FDX', 'MRVL', 'FICO', 'SPG', 'VST', 'NXPI', 'OKE', 'MPLX', 'GWW', 'LNG', 'SRE', 'PWR', 'PCAR', 'O', 'BDX', 'ROST', 'MPC', 'PSX', 'AMP', 'CPNG', 'AIG', 'TEL', 'GM', 'D', 'SLB', 'FAST', 'JD', 'URI', 'NDAQ', 'CTVA', 'KMB', 'CMI', 'KVUE', 'KDP', 'KR', 'EW', 'CCI', 'EXC', 'TGT', 'MSCI', 'FLUT', 'VRSK', 'LHX', 'F', 'FIS', 'VLO', 'AME', 'IDXX', 'XEL', 'OXY', 'YUM', 'CRWV', 'TTWO', 'GLW', 'HES', 'CCEP', 'FANG', 'VRT', 'LULU', 'DDOG', 'CTSH', 'PEG', 'GRMN', 'ZS', 'VEEV', 'PCG', 'CBRE', 'OTIS', 'DHI', 'PRU', 'ALNY', 'ED', 'EA', 'BKR', 'TTD', 'HIG', 'RMD', 'CAH', 'VMC', 'FERG', 'ODFL', 'ARES', 'XYZ', 'ETR', 'TRGP', 'ACGL', 'WAB', 'SYY', 'EFX', 'ROK', 'IT', 'TW', 'LYV', 'STZ', 'MLM', 'WEC', 'HUBS', 'HEI', 'DXCM', 'VICI', 'IR', 'MPWR', 'GEHC', 'DAL', 'EBAY', 'EQT', 'KHC', 'TPL', 'MCHP', 'TKO', 'CSGP', 'QSR', 'EXR', 'A', 'BRO', 'HSY', 'NRG', 'XYL', 'WTW', 'RJF', 'BIDU', 'FWONA', 'LPLA', 'CNC', 'CCL', 'ANSS', 'MTB', 'GIS', 'OWL', 'LVS', 'HUM', 'IRM', 'AVB', 'LEN', 'DD', 'DTE', 'K', 'BR', 'CQP', 'KEYS', 'TSCO', 'STT', 'AWK', 'WRB', 'ROL', 'HPQ', 'AEE', 'IOT', 'EQR', 'GDDY', 'EXE', 'SMCI', 'NUE', 'IP', 'VRSN', 'FITB', 'UI', 'PPG', 'RKT', 'PPL', 'TOST', 'UAL', 'DOV', 'FCNCA', 'ZM', 'ATO', 'VLTO', 'SBAC', 'IQV', 'STE', 'CDW', 'TYL', 'FE', 'FTV', 'TME', 'CPAY', 'CNP', 'VG', 'DRI', 'MKL', 'SW', 'FOX', 'MTD', 'ADM', 'CHKP', 'DUOL', 'CHD', 'CINF', 'BNTX', 'EL', 'CBOE', 'HBAN', 'ES', 'TDY', 'STX', 'HPE', 'PODD', 'SYF', 'WBD', 'EIX', 'CCJ', 'NTNX', 'OKTA', 'AMCR', 'DIDIY', 'PINS', 'GFS', 'DG', 'TROW', 'CMS', 'BIP', 'LII', 'WSM', 'NVR', 'WAT', 'DOW', 'AU', 'INVH', 'EXPE', 'EME', 'NTRS', 'DVN', 'NTAP', 'NTRA', 'LH', 'HUBB', 'VIK', 'GRAB', 'PTC', 'PHM', 'LDOS', 'RF', 'STLD', 'AER', 'MKC', 'RDDT', 'DGX', 'WSO', 'IFF', 'SSNC', 'GPN', 'TSN', 'ONON', 'DECK', 'RPRX', 'WY', 'LYB', 'BIIB', 'ZBH', 'MAA', 'XPEV', 'NI', 'TPG', 'L', 'CTRA', 'RIVN', 'LUV', 'ULTA', 'DOCU', 'DKNG', 'RYAN', 'ESS', 'PSTG', 'ON', 'PFG', 'DLTR', 'CRBG', 'KEY', 'GWRE', 'CFG', 'JBL', 'HAL', 'TRU', 'TECK', 'GPC', 'CHWY', 'USFD', 'FDS', 'SMMT', 'TWLO', 'WDC', 'FSLR', 'GEN', 'MOH', 'CSL', 'PKG', 'AS', 'ERIE', 'SNA', 'CG', 'CYBR', 'RL', 'TPR', 'TRMB', 'CNH', 'DPZ', 'BURL', 'CASY', 'NWS', 'CPT', 'BF.A', 'RBRK', 'SYM', 'AFRM', 'YUMC', 'CLX', 'FIX', 'PNR', 'HRL', 'SFM', 'FFIV', 'COO', 'BAH', 'EQH', 'Z', 'LNT', 'EXPD', 'BAX', 'RS', 'FLEX', 'DT', 'FNF', 'CW', 'SUI', 'BJ', 'WST', 'THC', 'J', 'MDB', 'EVRG', 'BAP', 'ARCC', 'SOFI', 'BBY', 'ZBRA', 'BALL', 'PAYC', 'OMC', 'WES', 'RPM', 'ALAB', 'XPO', 'EG', 'MNDY', 'APTV', 'KIM', 'DKS', 'ULS', 'BSY', 'GGG', 'JBHT', 'SNAP', 'ACM', 'AMH', 'AVY', 'IEX', 'UNM', 'WMG', 'SN', 'CF', 'LBRDA', 'MAS', 'UDR', 'HIMS', 'RGA', 'SGI', 'TXT', 'UTHR', 'PFGC', 'WPC', 'REG', 'JKHY', 'ALGN', 'CNA', 'ILMN', 'MORN', 'SOLV', 'EWBC', 'FTI', 'TER', 'GLPI', 'BLDR', 'APG', 'TXRH', 'ARE', 'MBLY', 'H', 'WWD', 'YMM', 'UHS', 'DOC', 'HOLX', 'ACI', 'FTAI', 'ELS', 'HLI', 'GME', 'CLH', 'ALLE', 'MTZ', 'INSM', 'INCY', 'COHR', 'AR', 'EHC', 'LAMR', 'EXEL', 'NBIX', 'POOL', 'OC', 'JNPR', 'SJM', 'RNR', 'ITT', 'PAA', 'CART', 'NLY', 'PRMB', 'RKLB', 'CHRW', 'RBC', 'BROS', 'CRS', 'TTAN', 'MANH', 'BEN', 'CCK', 'NDSN', 'PPC', 'CIEN', 'MMYT', 'UHAL', 'PHYS', 'TAP', 'ENTG', 'BMRN', 'RGLD', 'AKAM', 'LECO', 'MOS', 'DRS', 'SCI', 'CIB', 'RVTY', 'AUR', 'ALLY', 'PCTY', 'PAG', 'PNW', 'TEM', 'KNSL', 'JLL', 'CAG', 'WTRG', 'NVT', 'SWKS', 'LINE', 'DVA', 'TLN', 'FRHC', 'SWK', 'LKQ', 'PEN', 'OHI', 'ATI', 'BG', 'BXP', 'EXAS', 'HST', 'PR', 'SEIC', 'AFG', 'JEF', 'CPB', 'ICLR', 'TOL', 'BIRK', 'GAP', 'DTM', 'CRDO', 'CNM', 'CACI', 'ATR', 'SNX', 'PCOR', 'ARMK', 'CAVA', 'EPAM', 'ROKU', 'KMX', 'AIZ', 'FHN', 'VTRS', 'WLK', 'CR', 'DOX', 'SAIL', 'MRNA', 'COKE', 'SF', 'WYNN', 'DOCS', 'GL', 'BWXT', 'WIX', 'AOS', 'XP', 'SARO']
}

# this is the same as main_symbols except that each list will have sublists of a certain amount of symbols. The remaining symbols will be in the last sublist
symbol_set = {
    CURRENCIES_WEBHOOK_NAME: [], 
    CRYPTO_WEBHOOK_NAME: [], 
    INDIAN_STOCKS_WEBHOOK_NAME: [], 
    US_STOCKS_WEBHOOK_NAME: []
}

# this is a dictionary whose keys are the symbols and their values are the categories
symbol_categories = {}
for category, symbols in main_symbols.items():
    # Map each symbol to its category in symbol_categories. symbol has to be split so that the key can be just the symbol and not it's exchange eg: just EURUSD without the OANDA part
    symbol_categories.update({symbol.split(':')[-1]: category for symbol in symbols})  


def fill_symbol_set(symbol_inputs: int):
    '''This fills up the `symbol_set` dictionary. Every key's value is a list with sublists inside it. Each sublist has a maximum of `symbol_inputs` elements. The elements of those sublists are symbols.'''
    try:
        for category, symbols in main_symbols.items():
            sublists = [symbols[i:i+symbol_inputs] for i in range(0, len(symbols), symbol_inputs)]  # Split symbols into sublists of symbol_inputs
            if sublists and len(sublists[-1]) < symbol_inputs:  # If some symbols are remaining
                last_sublist = sublists.pop() if sublists else []  # Pop the last sublist if it exists
                sublists.append(last_sublist)  # Add the remaining symbols in a new sublist
            symbol_set[category] = sublists  # Fill up the symbol_set dictionary

        symbol_logger.info("Filled up symbol_set!")
        return True  # Return True if symbol_set is successfully filled up
    except Exception as e:
        symbol_logger.exception("Failed to fill up symbol_set.")
        return False

def symbol_category(symbol):
    '''
    This function returns the symbol category. It retrieves the category of `symbol` (the category can be a US stock, forex pair, crypto pair, etc.)
    '''
    return symbol_categories.get(symbol, None)