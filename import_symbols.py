"""
Import symbols from symbol_settings.py into Stock Buddy API

This script reads all symbols from the original TTE symbol_settings.py 
and imports them into the Stock Buddy database via the API.
"""

import requests
import json

API_BASE = "https://stock-buddy-app.vercel.app/api/tte"

# All symbols from symbol_settings.py
# Categories and their priorities:
# - Currencies (forex): Priority A (major pairs) and B (cross pairs)
# - Crypto: Priority B
# - Indian Stocks: Priority C
# - US Stocks: Priority C
# - Indices: Priority B

main_symbols = {
    "currencies": [
        "OANDA:GBPAUD",
        "OANDA:AUDJPY",
        "OANDA:EURCAD",
        "OANDA:EURGBP",
        "OANDA:USDCHF",
        "OANDA:AUDNZD",
        "OANDA:XAUUSD",
        "OANDA:WTIUSD",
        "OANDA:EURNZD",
        "OANDA:USDJPY",
        "OANDA:NZDJPY",
        "OANDA:GBPUSD",
        "OANDA:AUDCAD",
        "OANDA:EURJPY",
        "OANDA:GBPNZD",
        "OANDA:GBPJPY",
        "OANDA:EURUSD",
        "OANDA:EURCHF",
        "OANDA:GBPCAD",
        "OANDA:AUDUSD",
        "OANDA:XAGUSD",
        "OANDA:NZDUSD",
        "OANDA:EURAUD",
        "OANDA:CADCHF",
        "OANDA:CHFJPY",
        "OANDA:GBPCHF",
        "OANDA:NZDCHF",
        "OANDA:CADJPY",
        "OANDA:USDCAD",
        "OANDA:NZDCAD",
    ],
    "crypto": [
        "BINANCE:BTCUSDT",
        "BINANCE:BCHBTC",
        "BINANCE:DOGEUSDT",
        "BINANCE:TRXBTC",
        "BINANCE:UNIUSDT",
        "BINANCE:LTCUSDT",
        "BINANCE:LTCBTC",
        "BINANCE:BCHUSDT",
        "BINANCE:ETHUSDT",
        "BINANCE:XRPUSDT",
        "BINANCE:LINKBTC",
        "BINANCE:XRPBTC",
        "BINANCE:TRXUSDT",
        "BINANCE:XLMUSDT",
        "BINANCE:ETHBTC",
        "BINANCE:NEOUSDT",
        "BINANCE:EOSUSDT",
        "BINANCE:EOSBTC",
        "BINANCE:LINKUSDT",
    ],
    "indian_stocks": [
        "DEVYANI", "MMTC", "PRAJIND", "PTC", "JUBLFOOD", "NIACL", "SIEMENS", "TVTODAY",
        "TRENT", "M_M", "BAYERCROP", "ZENSARTECH", "MAHABANK", "MAHSEAMLES", "ABCAPITAL",
        "PRESTIGE", "BAJAJFINSV", "SCHNEIDER", "RELIANCE", "MASTEK", "VENKEYS", "PVR",
        "CHOLAFIN", "SYMPHONY", "QUESS", "COLPAL", "ACC", "MUTHOOTFIN", "NFL", "PETRONET",
        "KEC", "VAKRANGEE", "SCI", "CYIENT", "PGHH", "UPL", "THYROCARE", "SIS", "SUNPHARMA",
        "MRF", "FCSSOFT", "SONATSOFTW", "COFORGE", "MARUTI", "JUBLINDS", "SJVN", "CRISIL",
        "DABUR", "ITC", "MOTHERSON", "BALKRISIND", "COALINDIA", "LTI", "PAGEIND", "RBLBANK",
        "LICHSGFIN", "MGL", "AJANTPHARM", "TATASTEEL", "NESTLEIND", "EQUITASBNK", "BRITANNIA",
        "UNIONBANK", "KAJARIACER", "VIKASECO", "AIAENG", "KPRMILL", "SBILIFE", "APARINDS",
        "ESSENTIA", "SUNTV", "RAMCOCEM", "ASHOKLEY", "RCF", "GRANULES", "CANBK", "TITAN",
        "MIDHANI", "BLUESTARCO", "KANSAINER", "MCX", "HCC", "APOLLOTYRE", "TEXRAIL",
        "PRSMJOHNSN", "JINDALSTEL", "BANKINDIA", "BERGEPAINT", "BAJFINANCE", "HINDPETRO",
        "NCC", "JKCEMENT", "KOTAKBANK", "THERMAX", "AMBUJACEM", "MOIL", "JPASSOCIAT", "PFC",
        "SANOFI", "AUROPHARMA", "UCOBANK", "IFCI", "RALLIS", "HATHWAY", "TV18BRDCST",
        "KPITTECH", "MARICO", "BEL", "ABBOTINDIA", "CREDITACC", "PERSISTENT", "TATACOFFEE",
        "DMART", "PNB", "WHIRLPOOL", "WELCORP", "IOC", "NAUKRI", "KSCL", "UJJIVAN",
        "MANAPPURAM", "BANKBARODA", "POLYCAB", "APOLLOHOSP", "JSWENERGY", "INDUSINDBK",
        "LUPIN", "VEDL", "JKLAKSHMI", "JPPOWER", "STAR", "KRBL", "BHARTIARTL", "TATAPOWER",
        "ABFRL", "WESTLIFE", "CARBORUNIV", "PFIZER", "NETWORK18", "TATACOMM", "IIFL",
        "ICICIBANK", "ADANIENT", "ABB", "VIPIND", "SKFINDIA", "TVSMOTOR", "WOCKPHARMA",
        "INFIBEAM", "SBICARD", "ADANIENSOL", "BOSCHLTD", "JUSTDIAL", "MAHINDCIE", "HDFCBANK",
        "BHEL", "GICRE", "AUBANK", "LALPATHLAB", "BPCL", "TATAMOTORS", "WIPRO", "HONASA",
        "JMFINANCIL", "SOLARINDS", "ANGELONE", "RECLTD", "CIPLA", "BATAINDIA", "GODFRYPHLP",
        "IRB", "APLAPOLLO", "ASTRAL", "DEEPAKNTR", "SUPRAJIT", "BANDHANBNK", "YESBANK",
        "TECHM", "ADANIPOWER", "KARURVYSYA", "ORIENTCEM", "TATAMTRDVR", "MPHASIS",
        "TORNTPHARM", "ZEEL", "BHARATFORG", "COROMANDEL", "KTKBANK", "ULTRACEMCO", "NBCC",
        "3MINDIA", "CUMMINSIND", "TEAMLEASE", "BIOCON", "SOUTHBANK", "AXISBANK", "SCHAEFFLER",
        "LT", "JSWSTEEL", "DLF", "GM", "SWANENERGY", "UBL", "MFSL", "SPARC", "TATAELXSI",
        "BAJAJ_AUTO", "NRBBEARING", "RELCAPITAL", "SYNGENE", "LTTS", "WELSPUNLIV", "ONGC",
        "UFLEX", "IRCON", "ATGL", "VSTIND", "TORNTPOWER", "SUZLON", "ADANIPORTS", "CENTRALBK",
        "INDIGO", "NTPC", "VRLLOG", "DIVISLAB", "SHREECEM", "ASIANPAINT", "VBL", "RATNAMANI",
        "SAIL", "AIRTELPP", "DALBHARAT", "NBVENTURES", "DIXON", "VAIBHAVGBL", "IDFCFIRSTB",
        "PIDILITIND", "NATIONALUM", "GAIL", "DELHIVERY", "VGUARD", "BDL", "LINDEINDIA",
        "CONCOR", "MHRIL", "NOCIL", "NHPC", "AWL", "ALKEM", "SMLISUZU", "PIIND", "ZYDUSWELL",
        "CGPOWER", "GMDCLTD", "TVVISION", "POWERGRID", "TATACHEM", "TRIDENT", "TIMKEN",
        "ADANIGREEN", "BAJAJHLDNG", "TATAINVEST", "BSE", "OBEROIRLTY", "IBREALEST", "MRPL",
    ],
    "us_stocks": [
        "MSFT", "NVDA", "AAPL", "AMZN", "GOOG", "META", "BRK.A", "TSLA", "AVGO", "WMT",
        "JPM", "LLY", "V", "MA", "NFLX", "COST", "XOM", "ORCL", "PG", "HD", "JNJ", "BAC",
        "ABBV", "KO", "PLTR", "BABA", "UNH", "TMUS", "CRM", "PM", "CSCO", "GE", "IBM",
        "WFC", "CVX", "ABT", "MCD", "LIN", "NOW", "MS", "AXP", "DIS", "T", "ISRG", "ACN",
        "MRK", "UBER", "GS", "INTU", "VZ", "AMD", "RTX", "PEP", "ADBE", "BX", "BKNG",
        "NEE", "QCOM", "TJX", "ETN", "AMAT", "CAT", "UNP", "SPGI", "HON", "BA", "BLK",
        "C", "SCHW", "DE", "ADP", "BSX", "FI", "GILD", "BMY", "LOW", "ANET", "PLD", "SYK",
        "VRTX", "TT", "PNC", "AMGN", "MMC", "ADI", "MU", "PANW", "LMT", "SBUX", "KKR",
        "MDT", "KLAC", "INTC", "CB", "NKE", "COP", "SHW", "REGN", "CME", "ICE", "ELV",
        "CI", "SO", "AON", "DUK", "WM", "APO", "LRCX", "SNPS", "PH", "GD", "CDNS", "MCK",
        "USB", "TDG", "PYPL", "CEG", "MSI", "HUM", "CMG", "EQIX", "MCO", "CL", "CRWD",
        "ITW", "CTAS", "WELL", "MDLZ", "APH", "NOC", "HCA", "ZTS", "AJG", "PGR", "MMM",
        "CVS", "EOG", "SLB", "FCX", "EMR", "MAR", "ROP", "COF", "TFC", "ORLY", "BDX",
        "GEV", "WMB", "ECL", "HLT", "FDX", "GM", "TGT", "OXY", "PSX", "PSA", "ADSK",
        "AFL", "SPG", "NSC", "JCI", "CARR", "PCAR", "SRE", "DLR", "AIG", "TRV", "VLO",
        "FICO", "AZO", "AEP", "ABNB", "CPRT", "O", "KMI", "MSTR", "URI", "MPC", "NEM",
        "RCL", "FTNT", "NXPI", "PWR", "ALL", "MET", "AMP", "GWW", "TEL", "MSCI", "CMI",
        "BK", "AME", "PRU", "DFS", "MNST", "D", "PAYX", "KMB", "HES", "ROST", "LULU",
        "FAST", "CCI", "LHX", "RSG", "DHI", "ODFL", "A", "AEM", "APP", "KDP", "KVUE",
        "CTSH", "PCG", "OTIS", "EXC", "EA", "IR", "GEHC", "VMC", "XEL", "CTVA", "VRSK",
        "MLM", "STZ", "GIS", "ACGL", "OKE", "IDXX", "IRM", "PEG", "KHC", "PPG", "ED",
        "EW", "HWM", "HIG", "AXON", "CBRE", "SYY", "DD", "GRMN", "COR", "LEN", "RMD",
        "KR", "BKR", "GLW", "MCHP", "FANG", "EXR", "AVB", "VICI", "WAB", "NUE", "WTW",
        "EFX", "HPQ", "TSCO", "EQR", "MTB", "ROK", "DOV", "FCNCA", "ZM", "ATO", "VLTO",
        "SBAC", "IQV", "STE", "CDW", "TYL", "FE", "FTV", "TME", "CPAY", "CNP", "VG",
        "DRI", "MKL", "SW", "FOX", "MTD", "ADM", "CHKP", "DUOL", "CHD", "CINF", "BNTX",
        "EL", "CBOE", "HBAN", "ES", "TDY", "STX", "HPE", "PODD", "SYF", "WBD", "EIX",
        "CCJ", "NTNX", "OKTA", "AMCR", "DIDIY", "PINS", "GFS", "DG", "TROW", "CMS",
        "BIP", "LII", "WSM", "NVR", "WAT", "DOW", "AU", "INVH", "EXPE", "EME", "NTRS",
        "DVN", "NTAP", "NTRA", "LH", "HUBB", "VIK", "GRAB", "PTC", "PHM", "LDOS", "RF",
        "STLD", "AER", "MKC", "RDDT", "DGX", "WSO", "IFF", "SSNC", "GPN", "TSN", "ONON",
        "DECK", "RPRX", "WY", "LYB", "BIIB", "ZBH", "MAA", "XPEV", "NI", "TPG", "L",
        "CTRA", "RIVN", "LUV", "ULTA", "DOCU", "DKNG", "RYAN", "ESS", "PSTG", "ON",
        "PFG", "DLTR", "CRBG", "KEY", "GWRE", "CFG", "JBL", "HAL", "TRU", "TECK", "GPC",
        "CHWY", "USFD", "FDS", "SMMT", "TWLO", "WDC", "FSLR", "GEN", "MOH", "CSL", "PKG",
        "AS", "ERIE", "SNA", "CG", "CYBR", "RL", "TPR", "TRMB", "CNH", "DPZ", "BURL",
        "CASY", "NWS", "CPT", "BF.A", "RBRK", "SYM", "AFRM", "YUMC", "CLX", "FIX", "PNR",
        "HRL", "SFM", "FFIV", "COO", "BAH", "EQH", "Z", "LNT", "EXPD", "BAX", "RS",
        "FLEX", "DT", "FNF", "CW", "SUI", "BJ", "WST", "THC", "J", "MDB", "EVRG", "BAP",
        "ARCC", "SOFI", "BBY", "ZBRA", "BALL", "PAYC", "OMC", "WES", "RPM", "ALAB",
        "XPO", "EG", "MNDY", "APTV", "KIM", "DKS", "ULS", "BSY", "GGG", "JBHT", "SNAP",
        "ACM", "AMH", "AVY", "IEX", "UNM", "WMG", "SN", "CF", "LBRDA", "MAS", "UDR",
        "HIMS", "RGA", "SGI", "TXT", "UTHR", "PFGC", "WPC", "REG", "JKHY", "ALGN", "CNA",
        "ILMN", "MORN", "SOLV", "EWBC", "FTI", "TER", "GLPI", "BLDR", "APG", "TXRH",
        "ARE", "MBLY", "H", "WWD", "YMM", "UHS", "DOC", "HOLX", "ACI", "FTAI", "ELS",
        "HLI", "GME", "CLH", "ALLE", "MTZ", "INSM", "INCY", "COHR", "AR", "EHC", "LAMR",
        "EXEL", "NBIX", "POOL", "OC", "JNPR", "SJM", "RNR", "ITT", "PAA", "CART", "NLY",
        "PRMB", "RKLB", "CHRW", "RBC", "BROS", "CRS", "TTAN", "MANH", "BEN", "CCK",
        "NDSN", "PPC", "CIEN", "MMYT", "UHAL", "PHYS", "TAP", "ENTG", "BMRN", "RGLD",
        "AKAM", "LECO", "MOS", "DRS", "SCI", "CIB", "RVTY", "AUR", "ALLY", "PCTY", "PAG",
        "PNW", "TEM", "KNSL", "JLL", "CAG", "WTRG", "NVT", "SWKS", "LINE", "DVA", "TLN",
        "FRHC", "SWK", "LKQ", "PEN", "OHI", "ATI", "BG", "BXP", "EXAS", "HST", "PR",
        "SEIC", "AFG", "JEF", "CPB", "ICLR", "TOL", "BIRK", "GAP", "DTM", "CRDO", "CNM",
        "CACI", "ATR", "SNX", "PCOR", "ARMK", "CAVA", "EPAM", "ROKU", "KMX", "AIZ",
        "FHN", "VTRS", "WLK", "CR", "DOX", "SAIL", "MRNA", "COKE", "SF", "WYNN", "DOCS",
        "GL", "BWXT", "WIX", "AOS", "XP", "SARO",
    ],
    "indices": [
        "SP:SPX",
        "DJ:DJI", 
        "NASDAQ:NDX",
        "TVC:VIX",
        "TVC:DXY",
        "FX:EURUSD",
        "TVC:GOLD",
        "TVC:SILVER",
        "TVC:USOIL",
        "NIFTY",
        "BANKNIFTY",
        "SENSEX",
        "FTSE",
        "DAX",
        "CAC40",
        "NIKKEI",
        "HSI",
        "ASX200",
    ],
}

# Major forex pairs get Priority A
MAJOR_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "XAUUSD", "XAGUSD"
]

def parse_symbol(full_symbol, category):
    """Parse a symbol string and return symbol info dict."""

    # Add exchange prefix for categories that don't have them
    if ":" in full_symbol:
        # Already has prefix (currencies, crypto, some indices)
        symbol = full_symbol
    else:
        # Add appropriate prefix based on category
        if category == "indian_stocks":
            symbol = f"NSE:{full_symbol}"
        elif category == "us_stocks":
            symbol = f"NASDAQ:{full_symbol}"
        elif category == "indices":
            # Map known indices to their exchanges
            index_exchanges = {
                "NIFTY": "NSE",
                "BANKNIFTY": "NSE",
                "SENSEX": "BSE",
                "FTSE": "CAPITALCOM",
                "DAX": "CAPITALCOM",
                "CAC40": "CAPITALCOM",
                "NIKKEI": "TVC",
                "HSI": "HSI",
                "ASX200": "ASX",
            }
            exchange_prefix = index_exchanges.get(full_symbol, "TVC")
            symbol = f"{exchange_prefix}:{full_symbol}"
        else:
            symbol = full_symbol

    # Map category to exchange type (what API expects)
    category_to_exchange = {
        "currencies": "FX",
        "crypto": "CRYPTO",
        "indian_stocks": "STOCKS",
        "us_stocks": "STOCKS",
        "indices": "INDICES"
    }
    exchange = category_to_exchange.get(category, "STOCKS")

    # Extract base symbol for major pair check
    if ":" in full_symbol:
        base_symbol = full_symbol.split(":", 1)[1]
    else:
        base_symbol = full_symbol

    # Determine priority
    if category == "currencies":
        if base_symbol in MAJOR_PAIRS:
            priority = "A"
        else:
            priority = "B"
    elif category == "crypto":
        priority = "B"
    elif category == "indices":
        priority = "B"
    else:
        priority = "C"

    return {
        "symbol": symbol,
        "exchange": exchange,
        "priority": priority,
        "category": category
    }

def main():
    print("=" * 60)
    print("  TTE Symbol Import")
    print("=" * 60)
    print()
    
    # Parse all symbols
    all_symbols = []
    for category, symbols in main_symbols.items():
        for full_symbol in symbols:
            parsed = parse_symbol(full_symbol, category)
            all_symbols.append(parsed)
    
    print(f"Total symbols to import: {len(all_symbols)}")
    
    # Count by priority
    priority_counts = {"A": 0, "B": 0, "C": 0}
    for s in all_symbols:
        priority_counts[s["priority"]] += 1
    
    print(f"  Priority A: {priority_counts['A']}")
    print(f"  Priority B: {priority_counts['B']}")
    print(f"  Priority C: {priority_counts['C']}")
    print()
    
    # Count by category
    category_counts = {}
    for s in all_symbols:
        cat = s["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("By category:")
    for cat, count in category_counts.items():
        print(f"  {cat}: {count}")
    print()
    
    # Import to API
    print("Importing to Stock Buddy API...")
    try:
        response = requests.post(
            f"{API_BASE}/symbols/import",
            json={
                "symbols": all_symbols,
                "clearExisting": True  # Clear and reimport all
            },
            timeout=60
        )
        
        data = response.json()

        if response.status_code == 200 and data.get("success"):
            # API returns imported/total at root level, not under 'data'
            print(f"\n[OK] Import successful!")
            print(f"  Imported: {data.get('imported', 0)}")
            print(f"  Total in DB: {data.get('total', 0)}")
        else:
            print(f"\n[ERROR] Import failed: {data.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n[ERROR] Request failed: {e}")
    
    print()
    print("=" * 60)
    print("  Import Complete")
    print("=" * 60)
    
    print("\nNext steps:")
    print("  1. Run: python tiered_main.py --init")
    print("  2. Run: python tiered_main.py --single-cycle")

if __name__ == "__main__":
    main()
