## 📘 engine.py

import os
import time
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

NSE_URLS = {
    "NIFTY": "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
    "BANKNIFTY": "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"
}

def fetch_option_chain(symbol="BANKNIFTY"):
    """Fetch current option chain snapshot from NSE"""
    url = NSE_URLS[symbol]
    session = requests.Session()
    resp = session.get(url, headers=HEADERS).json()
    recs = []
    for row in resp['records']['data']:
        strike = row.get('strikePrice')
        expiry = row.get('expiryDate')
        ce, pe = row.get('CE', {}), row.get('PE', {})
        recs.append({
            "Symbol": symbol,
            "Expiry": expiry,
            "Strike": strike,
            "CE_LTP": ce.get('lastPrice'),
            "PE_LTP": pe.get('lastPrice'),
            "CE_OI": ce.get('openInterest'),
            "PE_OI": pe.get('openInterest')
        })
    return pd.DataFrame(recs).dropna()

def save_snapshot(symbol, folder):
    df = fetch_option_chain(symbol)
    fname = f"{symbol}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(folder, fname)
    df.to_csv(path, index=False)
    print("Saved snapshot:", path)

def run_paper(symbol, folder, pollsec, iters):
    os.makedirs(folder, exist_ok=True)
    for i in range(iters):
        save_snapshot(symbol, folder)
        time.sleep(pollsec)

def backtest(folder, sl, rr, riskpct, maxtrades, side):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".csv")])
    balance, results = 1000000, []
    for f in files:
        df = pd.read_csv(f)
        atm = df.iloc[df['Strike'].sub(df['Strike'].mean()).abs().idxmin()]
        ce_price, pe_price = atm['CE_LTP'], atm['PE_LTP']
        # pick direction AUTO = random (mocked by higher OI)
        if side == "AUTO":
            buy_price = ce_price if atm['CE_OI'] > atm['PE_OI'] else pe_price
        elif side == "CE": buy_price = ce_price
        else: buy_price = pe_price

        risk_amt = balance * riskpct
        sl_price = buy_price * (1 - sl)
        target_price = buy_price * (1 + rr*sl)
        outcome = "LOSS"
        exit_price = sl_price
        if buy_price < target_price: 
            outcome = "WIN"
            exit_price = target_price
        pnl = (exit_price - buy_price) * (risk_amt / buy_price)
        balance += pnl
        results.append({"file": f, "entry": buy_price, "exit": exit_price, "outcome": outcome, "pnl": pnl, "balance": balance})

    dfres = pd.DataFrame(results)
    print(dfres.tail())
    plt.plot(dfres['balance'])
    plt.title("Equity Curve")
    plt.show()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["paper","backtest"], required=True)
    ap.add_argument("--symbol", default="BANKNIFTY")
    ap.add_argument("--snapshots", default="./snapshots")
    ap.add_argument("--pollsec", type=int, default=60)
    ap.add_argument("--iters", type=int, default=10)
    ap.add_argument("--sl", type=float, default=0.3)
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--riskpct", type=float, default=0.02)
    ap.add_argument("--maxtrades", type=int, default=3)
    ap.add_argument("--side", choices=["AUTO","CE","PE"], default="AUTO")
    args = ap.parse_args()

    if args.mode == "paper":
        run_paper(args.symbol, args.snapshots, args.pollsec, args.iters)
    else:
        backtest(args.snapshots, args.sl, args.rr, args.riskpct, args.maxtrades, args.side)
