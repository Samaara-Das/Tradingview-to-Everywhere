"""One-off: pull all >40d running setups, check via Yahoo candles whether TP or SL was crossed.

Outputs JSON for both reports.
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import yfinance as yf
import pandas as pd

URI = "mongodb+srv://stockbuddy:gw3WznxO8Z4dCrdU@stock-buddy.8kc2y6.mongodb.net/?retryWrites=true&w=majority&appName=stock-buddy"

YF_SYMBOL_MAP = {
    # Currencies → Yahoo forex
    "NZDUSD": "NZDUSD=X",
    # US stocks: same ticker
    "MCO": "MCO", "NDAQ": "NDAQ", "CTAS": "CTAS", "CPRT": "CPRT",
    "AES": "AES", "AXON": "AXON", "FER": "FER", "AIG": "AIG", "SCHW": "SCHW",
    # Indian stocks: .NS suffix (NSE)
    "INDIGO": "INDIGO.NS", "POWERGRID": "POWERGRID.NS", "ATGL": "ATGL.NS",
    "WAAREEENER": "WAAREEENER.NS", "THYROCARE": "THYROCARE.NS",
    "SUPRAJIT": "SUPRAJIT.NS", "TRIVENI": "TRIVENI.NS", "PETRONET": "PETRONET.NS",
    "MAHLIFE": "MAHLIFE.NS", "HDFCBANK": "HDFCBANK.NS", "BAJAJFINSV": "BAJAJFINSV.NS",
    "MUTHOOTFIN": "MUTHOOTFIN.NS", "UPL": "UPL.NS", "EICHERMOT": "EICHERMOT.NS",
}

def parse_entry_time(ms_str: str) -> datetime:
    # entryTime stored as string of float ms-since-epoch
    return datetime.fromtimestamp(float(ms_str) / 1000.0, tz=timezone.utc)

def main():
    c = MongoClient(URI, serverSelectionTimeoutMS=20000)
    cutoff = datetime.now(timezone.utc) - timedelta(days=40)
    cutoff_ms = str(cutoff.timestamp() * 1000)
    docs = list(c.tte.setup_messages.find({"outcome": "running"}))
    long_running = []
    now = datetime.now(timezone.utc)
    for d in docs:
        try:
            et = parse_entry_time(d["entryTime"])
        except Exception:
            continue
        age = (now - et).days
        if age >= 40:
            long_running.append({
                "symbol": d["symbol"],
                "direction": d["direction"],  # raw
                "entry": float(d["entryPrice"]),
                "tp": float(d["takeProfit"]),
                "sl": float(d["stopLoss"]),
                "entryTime": et.isoformat(),
                "ageDays": age,
                "nweTf": d.get("nweTf"),
                "obTf": d.get("obTf"),
                "label": d.get("label"),
            })
    long_running.sort(key=lambda x: -x["ageDays"])
    print(f"Found {len(long_running)} running setups >=40d old", file=sys.stderr)

    # For each, fetch daily candles since entryTime, check raw TP/SL cross
    results = []
    for s in long_running:
        sym = s["symbol"]
        yf_sym = YF_SYMBOL_MAP.get(sym)
        if not yf_sym:
            s["yahoo_status"] = "no_mapping"
            results.append(s)
            continue
        start = (datetime.fromisoformat(s["entryTime"]) - timedelta(days=1)).date()
        try:
            t = yf.Ticker(yf_sym)
            hist = t.history(start=start.isoformat(), interval="1d", auto_adjust=False)
        except Exception as e:
            s["yahoo_status"] = f"err:{e}"
            results.append(s)
            continue
        if hist is None or hist.empty:
            s["yahoo_status"] = "empty"
            results.append(s)
            continue
        # Check raw direction crosses:
        # raw Sell: TP < entry < SL. TP-hit if low <= TP. SL-hit if high >= SL.
        # raw Buy:  SL < entry < TP. TP-hit if high >= TP. SL-hit if low <= SL.
        tp = s["tp"]; sl = s["sl"]; dirn = s["direction"]
        tp_hit_date = None; sl_hit_date = None
        max_high = float(hist["High"].max())
        min_low = float(hist["Low"].min())
        for idx, row in hist.iterrows():
            if dirn == "Sell":
                if tp_hit_date is None and row["Low"] <= tp:
                    tp_hit_date = idx.date().isoformat()
                if sl_hit_date is None and row["High"] >= sl:
                    sl_hit_date = idx.date().isoformat()
            else:  # Buy
                if tp_hit_date is None and row["High"] >= tp:
                    tp_hit_date = idx.date().isoformat()
                if sl_hit_date is None and row["Low"] <= sl:
                    sl_hit_date = idx.date().isoformat()
            if tp_hit_date and sl_hit_date:
                break
        s["yahoo_status"] = "ok"
        s["bars"] = len(hist)
        s["maxHigh_since_entry"] = max_high
        s["minLow_since_entry"] = min_low
        s["raw_tp_hit_date"] = tp_hit_date
        s["raw_sl_hit_date"] = sl_hit_date
        results.append(s)

    out_path = "scripts/investigate_stale.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Wrote {out_path}", file=sys.stderr)
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    main()
