import os
import time
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime
import numpy as np  # <— needed for Sharpe calc

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
    os.makedirs(folder, exist_ok=True)
    df = fetch_option_chain(symbol)
    fname = f"{symbol}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(folder, fname)
    df.to_csv(path, index=False)
    print("Saved snapshot:", path)

def run_paper(symbol, folder, pollsec, iters):
    os.makedirs(folder, exist_ok=True)
    for _ in range(iters):
        save_snapshot(symbol, folder)
        time.sleep(pollsec)

def _extract_date_from_filename(fname: str) -> datetime.date:
    # expects like: BANKNIFTY_20250901_190646.csv
    date_str = os.path.basename(fname).split("_")[1][:8]
    return datetime.datetime.strptime(date_str, "%Y%m%d").date()

def backtest(folder, sl, rr, riskpct, maxtrades, side, export_csv=True):
    """
    Backtest with:
      Run backtest with daily risk controls
      - sl: stoploss %
      - rr: risk:reward ratio
      - riskpct: % of balance risked per trade
      - maxtrades: max trades per day
      - side: AUTO / CE / PE
      - Look-ahead exit logic (as in your running version)
      - Fixed daily risk controls: -1% stop-loss, +2% profit target
      - Max trades per day via --maxtrades
      - Trade-level stop_flag + Daily summary with stop_reason
      - Sharpe, Max Drawdown, equity curve + histogram
    """
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".csv")])
    if not files:
        print("No snapshot CSVs found in:", folder)
        return

    balance = 1000000.0
    results = []

    # Daily controls (fixed 1:2)
    max_daily_loss = 0.01     # -1%
    max_daily_profit = 0.02   # +2%

    trades_today = 0
    last_date = None
    day_start_balance = balance
    day_stopped = False  # track if day already stopped by rule

    for i, f in enumerate(files[:-1]):  # stop at second last file (we look ahead)
        trade_date = _extract_date_from_filename(f)

        # Reset on new day
        if last_date != trade_date:
            last_date = trade_date
            trades_today = 0
            day_start_balance = balance
            day_stopped = False

        # Enforce daily trade limit
        if trades_today >= maxtrades:
            continue

        # Enforce daily risk stops BEFORE new trade if already tripped
        day_pnl_pct = (balance - day_start_balance) / day_start_balance if day_start_balance != 0 else 0
        if day_stopped or day_pnl_pct <= -max_daily_loss or day_pnl_pct >= max_daily_profit:
            day_stopped = True
            continue

        # Read entry snapshot
        df = pd.read_csv(f)
        if df.empty:
            continue

        # Choose ATM row by proximity to mean strike (as in your code)
        atm = df.iloc[df['Strike'].sub(df['Strike'].mean()).abs().idxmin()]
        ce_price, pe_price = float(atm['CE_LTP']), float(atm['PE_LTP'])

        # Direction logic
        if side == "AUTO":
            contract = "CE" if atm['CE_OI'] > atm['PE_OI'] else "PE"
            buy_price = ce_price if contract == "CE" else pe_price
        elif side == "CE":
            contract, buy_price = "CE", ce_price
        else:
            contract, buy_price = "PE", pe_price

        if buy_price is None or buy_price <= 0:
            continue

        # Risk per trade & levels
        risk_amt = balance * riskpct
        sl_price = buy_price * (1 - sl)
        target_price = buy_price * (1 + rr * sl)

        # --- Look-ahead logic (unchanged intent):
        # Iterate forward a few snapshots (up to maxtrades window) to see if SL/TP hits
        hit, exit_price, outcome = None, None, None
        lookahead_end = min(i + 1 + maxtrades, len(files))
        for j in range(i + 1, lookahead_end):
            f2 = files[j]
            df_future = pd.read_csv(f2)
            if df_future.empty:
                continue
            atm_future = df_future.iloc[df_future['Strike'].sub(df_future['Strike'].mean()).abs().idxmin()]
            future_price = float(atm_future[f"{contract}_LTP"])

            if future_price <= sl_price:
                hit, exit_price, outcome = "SL", sl_price, "LOSS"
                break
            elif future_price >= target_price:
                hit, exit_price, outcome = "TARGET", target_price, "WIN"
                break

        # If neither SL/TP hit, close at the last seen future price within window
        if not hit:
            df_future = pd.read_csv(files[lookahead_end - 1])
            atm_future = df_future.iloc[df_future['Strike'].sub(df_future['Strike'].mean()).abs().idxmin()]
            future_price = float(atm_future[f"{contract}_LTP"])
            exit_price, outcome = future_price, "HOLD"

        # PnL & balance update
        position_size = risk_amt / buy_price if buy_price != 0 else 0
        pnl = (exit_price - buy_price) * position_size
        balance += pnl
        trades_today += 1

        # After the trade, check if daily stop/profit got hit
        stop_flag = ""
        day_pnl_pct_after = (balance - day_start_balance) / day_start_balance if day_start_balance != 0 else 0
        if day_pnl_pct_after <= -max_daily_loss:
            stop_flag = "STOPPED by Daily Loss Limit"
            day_stopped = True
        elif day_pnl_pct_after >= max_daily_profit:
            stop_flag = "STOPPED by Daily Profit Target"
            day_stopped = True

        results.append({
            "file": os.path.basename(f),
            "date": trade_date.isoformat(),
            "side": contract,
            "entry": buy_price,
            "exit": exit_price,
            "outcome": outcome,
            "pnl": pnl,
            "balance": balance,
            "stop_flag": stop_flag
        })

    # --- Results DataFrame ---
    dfres = pd.DataFrame(results)
    if dfres.empty:
        print("No trades executed.")
        return

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

    # Sharpe ratio (trades as returns; rf=0)
    # normalize by entry to approximate per-trade return
    returns = dfres['pnl'] / dfres['entry'].replace(0, np.nan)
    returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std(ddof=0) != 0 else 0

    # Max Drawdown
    equity = dfres['balance']
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    max_dd = float(drawdown.min()) * 100 if not drawdown.empty else 0.0

    print("\n📈 Backtest Summary")
    print(f" Total Trades: {total_trades}")
    print(f" Wins: {wins}, Losses: {losses}, Holds: {holds}")
    print(f" Win Rate: {win_rate:.2f}%")
    print(f" Avg PnL per trade: {avg_pnl:.2f}")
    print(f" Final Balance: {final_balance:.2f}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Max Drawdown: {max_dd:.2f}%")

    # --- Save to CSVs ---
    if export_csv:
        out_path = os.path.join(folder, "backtest_results.csv")
        dfres.to_csv(out_path, index=False)
        print(f"\n✅ Trade history exported: {out_path}")

    # Daily summary with stop_reason
    daily = dfres.groupby("date").agg(
        trades=("outcome", "count"),
        wins=("outcome", lambda x: (x == "WIN").sum()),
        losses=("outcome", lambda x: (x == "LOSS").sum()),
        holds=("outcome", lambda x: (x == "HOLD").sum()),
        day_pnl=("pnl", "sum"),
        close_balance=("balance", "last")
    ).reset_index()

    # Compute stop_reason using trade-level flags or day-level PnL
    daily["stop_reason"] = "ACTIVE"
    for irow, row in daily.iterrows():
        d = row["date"]
        day_trades = dfres[dfres["date"] == d]
        # If any trade has a stop_flag, use it
        flags = day_trades["stop_flag"].dropna().unique().tolist()
        if any("Loss" in f for f in flags):
            daily.at[irow, "stop_reason"] = "STOPPED by Daily Loss Limit"
        elif any("Profit" in f for f in flags):
            daily.at[irow, "stop_reason"] = "STOPPED by Daily Profit Target"
        else:
            # derive from PnL if needed
            day_start = day_trades["balance"].iloc[0] - day_trades["pnl"].iloc[0]
            day_end = day_trades["balance"].iloc[-1]
            day_pnl_pct2 = (day_end - day_start) / day_start if day_start != 0 else 0
            if day_pnl_pct2 <= -max_daily_loss:
                daily.at[irow, "stop_reason"] = "STOPPED by Daily Loss Limit"
            elif day_pnl_pct2 >= max_daily_profit:
                daily.at[irow, "stop_reason"] = "STOPPED by Daily Profit Target"

    daily_path = os.path.join(folder, "daily_summary.csv")
    daily.to_csv(daily_path, index=False)
    print(f"✅ Daily summary exported: {daily_path}")

    # --- Charts ---

    # 1) Equity curve with stop markers
    plt.figure(figsize=(10, 6))
    plt.plot(dfres.index, dfres['balance'], label="Equity Curve")
    stop_loss_points = dfres[dfres["stop_flag"].str.contains("Loss", na=False)]
    stop_profit_points = dfres[dfres["stop_flag"].str.contains("Profit", na=False)]
    plt.scatter(stop_loss_points.index, stop_loss_points["balance"], marker="o", s=80, label="Daily Stop Loss Hit")
    plt.scatter(stop_profit_points.index, stop_profit_points["balance"], marker="o", s=80, label="Daily Profit Target Hit")
    plt.title("Equity Curve with Daily Stop Markers")
    plt.xlabel("Trades")
    plt.ylabel("Balance")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()

    # 2) Equity + PnL histogram (as in your original layout)
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(dfres['balance'])
    plt.title("Equity Curve")
    plt.xlabel("Trades")
    plt.ylabel("Balance")

    plt.subplot(1, 2, 2)
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
    ap.add_argument("--maxtrades", type=int, default=3)  # interpreted as max trades per DAY
    ap.add_argument("--side", choices=["AUTO","CE","PE"], default="AUTO")
    args = ap.parse_args()

    if args.mode == "paper":
        run_paper(args.symbol, args.snapshots, args.pollsec, args.iters)
    else:
        backtest(args.snapshots, args.sl, args.rr, args.riskpct, args.maxtrades, args.side)
