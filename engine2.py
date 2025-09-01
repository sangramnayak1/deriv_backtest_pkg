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

def backtest(folder, sl, rr, riskpct, maxtrades, side, export_csv=True):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".csv")])
    balance, results = 1000000, []

    for i, f in enumerate(files[:-1]):  # stop at second last file
        df = pd.read_csv(f)
        atm = df.iloc[df['Strike'].sub(df['Strike'].mean()).abs().idxmin()]
        ce_price, pe_price = atm['CE_LTP'], atm['PE_LTP']

        # pick direction AUTO = mock OI-based bias
        if side == "AUTO":
            buy_price = ce_price if atm['CE_OI'] > atm['PE_OI'] else pe_price
            contract = "CE" if atm['CE_OI'] > atm['PE_OI'] else "PE"
        elif side == "CE":
            buy_price, contract = ce_price, "CE"
        else:
            buy_price, contract = pe_price, "PE"

        risk_amt = balance * riskpct
        sl_price = buy_price * (1 - sl)
        target_price = buy_price * (1 + rr * sl)

        # look ahead in future snapshots
        hit, exit_price, outcome = None, None, None
        for j in range(i+1, min(i+1+maxtrades, len(files))):
            f2 = files[j]
            df_future = pd.read_csv(f2)
            atm_future = df_future.iloc[df_future['Strike'].sub(df_future['Strike'].mean()).abs().idxmin()]
            future_price = atm_future[f"{contract}_LTP"]

            if future_price <= sl_price:
                hit, exit_price, outcome = "SL", sl_price, "LOSS"
                break
            elif future_price >= target_price:
                hit, exit_price, outcome = "TARGET", target_price, "WIN"
                break

        # if neither hit, close at last available price
        if not hit:
            df_future = pd.read_csv(files[min(i+maxtrades, len(files)-1)])
            atm_future = df_future.iloc[df_future['Strike'].sub(df_future['Strike'].mean()).abs().idxmin()]
            future_price = atm_future[f"{contract}_LTP"]
            exit_price, outcome = future_price, "HOLD"

        pnl = (exit_price - buy_price) * (risk_amt / buy_price)
        balance += pnl

        results.append({
            "file": os.path.basename(f),
            "side": contract,
            "entry": buy_price,
            "exit": exit_price,
            "outcome": outcome,
            "pnl": pnl,
            "balance": balance
        })

    dfres = pd.DataFrame(results)
    print("\n📊 Last 5 trades:")
    print(dfres.tail())

    # --- Analytics ---
    total_trades = len(dfres)
    wins = (dfres['outcome'] == "WIN").sum()
    losses = (dfres['outcome'] == "LOSS").sum()
    holds = (dfres['outcome'] == "HOLD").sum()

    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
    avg_pnl = dfres['pnl'].mean()
    final_balance = dfres['balance'].iloc[-1]

    # Sharpe ratio (assuming trades ~ daily returns, rf=0)
    returns = dfres['pnl'] / (dfres['entry'])  # normalized per trade
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0

    # Max Drawdown
    equity = dfres['balance']
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    max_dd = drawdown.min() * 100  # %

    print("\n📈 Backtest Summary")
    print(f" Total Trades: {total_trades}")
    print(f" Wins: {wins}, Losses: {losses}, Holds: {holds}")
    print(f" Win Rate: {win_rate:.2f}%")
    print(f" Avg PnL per trade: {avg_pnl:.2f}")
    print(f" Final Balance: {final_balance:.2f}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Max Drawdown: {max_dd:.2f}%")

    # --- Save to CSV ---
    if export_csv:
        out_path = os.path.join(folder, "backtest_results.csv")
        dfres.to_csv(out_path, index=False)
        print(f"\n✅ Trade history exported: {out_path}")

    # --- Charts ---
    plt.figure(figsize=(12,5))

    # Equity curve
    plt.subplot(1,2,1)
    plt.plot(dfres['balance'])
    plt.title("Equity Curve")
    plt.xlabel("Trades")
    plt.ylabel("Balance")

    # PnL histogram
    plt.subplot(1,2,2)
    plt.hist(dfres['pnl'], bins=30, edgecolor="black")
    plt.title("PnL Distribution")
    plt.xlabel("PnL per Trade")
    plt.ylabel("Frequency")

    plt.tight_layout()
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
