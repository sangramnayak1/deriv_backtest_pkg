#!/usr/bin/env python3
"""
strategy_builder_greeks.py

Interactive + Prebuilt option strategy builder that evaluates strategy value BEFORE EXPIRY
using Black-Scholes (via mibian).

Features:
- Interactive mode to add legs (CALL/PUT, BUY/SELL, Strike, Qty).
- Prebuilt mode (Straddle, Strangle, Bull Call Spread, Iron Condor).
- Computes theoretical premium & Greeks per leg using BS, or accepts manual premium.
- Simulates strategy value and Greeks across:
    - spot price grid (±20% by default)
    - time slices (list of days to expiry, e.g., t0, mid, near, expiry)
- Plots:
    - PnL (strategy value - initial cost) at different time slices
    - Aggregated Delta/Theta/Vega curves vs strike/spot at selected times
    - Payoff at expiry
- Prints max profit/loss and breakevens at expiry.

Author: ChatGPT (adapted for Indian index options)
"""

import datetime
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mibian

# ---------- Helpers: Black-Scholes via mibian ----------
def bs_option(spot, strike, rate_pct, days, iv_pct, contract="CALL"):
    """
    Return theoretical price and Greeks using mibian Black-Scholes.
    - spot: underlying price
    - strike: strike price
    - rate_pct: interest rate in percent (annual)
    - days: days to expiry (integer)
    - iv_pct: implied volatility in percent (annual)
    - contract: "CALL" or "PUT"
    Returns dict: price, delta, gamma, theta, vega
    """
    # mibian expects: [underlying, strike, interest_rate_percent, days_to_expiry]
    bs = mibian.BS([spot, strike, rate_pct, max(1, int(round(days)))], volatility=iv_pct)
    # mibian returns callPrice/putPrice, callDelta/putDelta, gamma, callTheta/putTheta, vega
    if contract == "CALL":
        price = float(bs.callPrice)
        delta = float(bs.callDelta)
        theta = float(bs.callTheta)
    else:
        price = float(bs.putPrice)
        delta = float(bs.putDelta)
        theta = float(bs.putTheta)
    gamma = float(bs.gamma)
    vega = float(bs.vega)
    return {"price": price, "delta": delta, "gamma": gamma, "theta": theta, "vega": vega}

# ---------- Payoff/simple helpers ----------
def payoff_call_intrinsic(spot, strike, premium, qty=1, short=False):
    val = np.maximum(spot - strike, 0) - premium
    return (-qty * val) if short else (qty * val)

def payoff_put_intrinsic(spot, strike, premium, qty=1, short=False):
    val = np.maximum(strike - spot, 0) - premium
    return (-qty * val) if short else (qty * val)

# ---------- Strategy evaluation ----------
def evaluate_strategy(legs, spot_grid, days_to_expiry_list, rate_pct, iv_pct):
    """
    Evaluate strategy value and aggregated Greeks at multiple time slices.

    legs: list of dicts:
        {"type":"CALL"/"PUT", "strike":int, "qty":int, "side":"BUY"/"SELL", "premium":float (optional)}
    spot_grid: 1D numpy array of spot points
    days_to_expiry_list: list of days (integers) to evaluate, e.g. [T0, mid, 1, 0]
    rate_pct: interest rate percent
    iv_pct: implied volatility percent (we assume same IV for all strikes here; you can modify per-strike)
    Returns:
        results: dict keyed by days -> dict with keys:
            "value_by_spot" (numpy array), "delta_by_spot", "theta_by_spot", "vega_by_spot"
    """
    results = {}

    # initial theoretical premiums if not provided for legs (we compute at days_to_expiry_list[0])
    t0 = days_to_expiry_list[0]
    for leg in legs:
        if "premium" not in leg or leg["premium"] is None:
            b = bs_option(spot=spot_grid[len(spot_grid)//2], strike=leg["strike"],
                          rate_pct=rate_pct, days=t0, iv_pct=iv_pct, contract="CALL" if leg["type"]=="CALL" else "PUT")
            leg["premium"] = b["price"]

    for days in days_to_expiry_list:
        value_by_spot = np.zeros_like(spot_grid, dtype=float)
        delta_by_spot = np.zeros_like(spot_grid, dtype=float)
        theta_by_spot = np.zeros_like(spot_grid, dtype=float)
        vega_by_spot = np.zeros_like(spot_grid, dtype=float)
        gamma_by_spot = np.zeros_like(spot_grid, dtype=float)

        for idx, s in enumerate(spot_grid):
            total_val = 0.0
            total_delta = 0.0
            total_theta = 0.0
            total_vega = 0.0
            total_gamma = 0.0
            for leg in legs:
                typ = leg["type"]
                strike = leg["strike"]
                qty = leg["qty"]
                short = (leg["side"].upper() == "SELL")
                premium = leg["premium"]

                # Use BS for theoretical price and Greeks at this time-to-expiry
                # Note: when days == 0 (expiry), BS returns something (we used max(1,days) earlier)
                metrics = bs_option(s, strike, rate_pct, days, iv_pct, contract=typ)
                theoretical_price = metrics["price"]
                delta = metrics["delta"]
                theta = metrics["theta"]
                vega = metrics["vega"]
                gamma = metrics["gamma"]

                # For position sign:
                sign = -1 if short else 1  # BUY positive payout for long (we consider position value)
                # Strategy value (mark-to-market) contribution from leg:
                leg_value = sign * qty * theoretical_price
                # Leg Greeks contribution (note: for short sign flips)
                leg_delta = sign * qty * delta
                leg_theta = sign * qty * theta
                leg_vega = sign * qty * vega
                leg_gamma = sign * qty * gamma

                total_val += leg_value
                total_delta += leg_delta
                total_theta += leg_theta
                total_vega += leg_vega
                total_gamma += leg_gamma

            value_by_spot[idx] = total_val
            delta_by_spot[idx] = total_delta
            theta_by_spot[idx] = total_theta
            vega_by_spot[idx] = total_vega
            gamma_by_spot[idx] = total_gamma

        results[days] = {
            "value_by_spot": value_by_spot,
            "delta_by_spot": delta_by_spot,
            "theta_by_spot": theta_by_spot,
            "vega_by_spot": vega_by_spot,
            "gamma_by_spot": gamma_by_spot
        }
    return results

# ---------- Analysis helpers ----------
def compute_initial_cost(legs):
    """Initial cost (cash outflow) of establishing strategy using leg['premium'] and signs"""
    cost = 0.0
    for leg in legs:
        sign = 1 if leg["side"].upper() == "BUY" else -1  # BUY = pay premium (+cost), SELL = receive premium (negative cost)
        cost += sign * leg["premium"] * leg["qty"]
    return cost

def analyze_expiry(spot_grid, expiry_value_by_spot, initial_cost):
    """
    From expiry_value_by_spot (strategy MTM at expiry) compute PnL (MTM - initial_cost),
    max profit, max loss, and breakevens (approx by sign changes).
    """
    pnl = expiry_value_by_spot - initial_cost
    max_profit = np.max(pnl)
    max_loss = np.min(pnl)
    # find approximate breakevens where pnl crosses zero
    bes = []
    for i in range(1, len(spot_grid)):
        if pnl[i-1] <= 0 < pnl[i] or pnl[i-1] >= 0 > pnl[i]:
            # linear interpolation to find approximate BE point
            x0, x1 = spot_grid[i-1], spot_grid[i]
            y0, y1 = pnl[i-1], pnl[i]
            if (y1 - y0) != 0:
                be = x0 - y0 * (x1 - x0) / (y1 - y0)
                bes.append(round(be, 2))
    return pnl, max_profit, max_loss, bes

# ---------- Strategy templates ----------
def build_prebuilt(strategy_name, df_chain=None, spot=None):
    """
    strategy_name: one of ("long_straddle","short_straddle","long_strangle","bull_call_spread","iron_condor")
    If df_chain provided (DataFrame of chain with CE_LTP/PE_LTP), we pull premiums; otherwise premiums set to None (BS used).
    """
    s = strategy_name.lower()
    legs = []
    atm_strike = None
    if df_chain is not None and spot is not None:
        atm_strike = min(df_chain['Strike'].values.tolist(), key=lambda x: abs(x - spot))
    # helper to fetch premium
    def premium_for(strike, typ):
        if df_chain is None:
            return None
        row = df_chain[df_chain["Strike"] == strike]
        if row.empty:
            return None
        return float(row.iloc[0]["CE_LTP"] if typ=="CALL" else row.iloc[0]["PE_LTP"])

    if s == "long_straddle":
        k = atm_strike
        legs = [
            {"type":"CALL","strike":k,"qty":1,"side":"BUY","premium":premium_for(k,"CALL")},
            {"type":"PUT","strike":k,"qty":1,"side":"BUY","premium":premium_for(k,"PUT")},
        ]
    elif s == "short_straddle":
        k = atm_strike
        legs = [
            {"type":"CALL","strike":k,"qty":1,"side":"SELL","premium":premium_for(k,"CALL")},
            {"type":"PUT","strike":k,"qty":1,"side":"SELL","premium":premium_for(k,"PUT")},
        ]
    elif s == "long_strangle":
        k1 = atm_strike - 200
        k2 = atm_strike + 200
        legs = [
            {"type":"PUT","strike":k1,"qty":1,"side":"BUY","premium":premium_for(k1,"PUT")},
            {"type":"CALL","strike":k2,"qty":1,"side":"BUY","premium":premium_for(k2,"CALL")},
        ]
    elif s == "bull_call_spread":
        k1 = atm_strike
        k2 = atm_strike + 200
        legs = [
            {"type":"CALL","strike":k1,"qty":1,"side":"BUY","premium":premium_for(k1,"CALL")},
            {"type":"CALL","strike":k2,"qty":1,"side":"SELL","premium":premium_for(k2,"CALL")},
        ]
    elif s == "iron_condor":
        # short OTM put, buy further OTM put, short OTM call, buy further OTM call
        kP_sell = atm_strike - 200
        kP_buy = atm_strike - 400
        kC_sell = atm_strike + 200
        kC_buy = atm_strike + 400
        legs = [
            {"type":"PUT","strike":kP_sell,"qty":1,"side":"SELL","premium":premium_for(kP_sell,"PUT")},
            {"type":"PUT","strike":kP_buy,"qty":1,"side":"BUY","premium":premium_for(kP_buy,"PUT")},
            {"type":"CALL","strike":kC_sell,"qty":1,"side":"SELL","premium":premium_for(kC_sell,"CALL")},
            {"type":"CALL","strike":kC_buy,"qty":1,"side":"BUY","premium":premium_for(kC_buy,"CALL")},
        ]
    else:
        raise ValueError("Unknown prebuilt strategy")
    return legs

# ---------- CLI / Interactive ----------
def interactive_build_from_chain(df_chain, spot):
    legs = []
    print("\nInteractive builder. Type 'done' at Option Type prompt to finish.")
    while True:
        typ = input("Option Type (CALL/PUT) or 'done': ").strip().upper()
        if typ == "DONE":
            break
        if typ not in ("CALL","PUT"):
            print("Type must be CALL or PUT")
            continue
        try:
            strike = int(input("Strike (integer): ").strip())
            side = input("Side (BUY/SELL): ").strip().upper()
            qty = int(input("Quantity (integer): ").strip())
        except Exception as e:
            print("Invalid input, try again.", e)
            continue
        # premium choice
        use_market = input("Use chain premium for this strike? (y/n): ").strip().lower() == "y"
        premium = None
        if use_market:
            row = df_chain[df_chain["Strike"] == strike] if df_chain is not None else pd.DataFrame()
            if row.empty:
                print("Strike not present in chain; will use theoretical BS premium.")
            else:
                premium = float(row.iloc[0]["CE_LTP"] if typ=="CALL" else row.iloc[0]["PE_LTP"])
        legs.append({"type":typ,"strike":strike,"qty":qty,"side":side,"premium":premium})
        print(f"Added leg: {legs[-1]}")
    return legs

def run_cli():
    print("=== Option Strategy Builder with Greeks (Before Expiry) ===")
    symbol = input("Symbol (just for reference, e.g., NIFTY/BANKNIFTY). leave blank if none: ").strip().upper()
    # Ask user for market inputs
    spot = float(input("Underlying spot price (e.g., 45000): ").strip())
    days_to_expiry = int(input("Days to expiry (integer, e.g., 10): ").strip())
    iv_pct = float(input("Implied Volatility % (annual, e.g., 15): ").strip())
    rate_pct = float(input("Risk-free rate % (annual, e.g., 6): ").strip() or 6)
    mode = input("Mode: (interactive / prebuilt): ").strip().lower()
    df_chain = None
    # If user wants, they can paste a simple CSV path for chain to use market premiums
    use_chain = input("Do you have a snapshot CSV of option chain to use market premiums? (y/n): ").strip().lower() == "y"
    if use_chain:
        path = input("Path to CSV (columns: Strike, CE_LTP, PE_LTP, optional): ").strip()
        try:
            df_chain = pd.read_csv(path)
        except Exception as e:
            print("Failed to read chain CSV:", e)
            df_chain = None

    if mode == "prebuilt":
        print("Select prebuilt strategy:")
        print("1: Long Straddle\n2: Short Straddle\n3: Long Strangle\n4: Bull Call Spread\n5: Iron Condor")
        choice = input("Choice (1-5): ").strip()
        map_choice = {"1":"long_straddle","2":"short_straddle","3":"long_strangle","4":"bull_call_spread","5":"iron_condor"}
        strat = map_choice.get(choice, "long_straddle")
        legs = build_prebuilt(strat, df_chain=df_chain, spot=spot)
    else:
        legs = interactive_build_from_chain(df_chain, spot)

    if not legs:
        print("No legs defined. Exiting.")
        return

    # Let user confirm/modify premiums or accept theoretical BS
    for leg in legs:
        if leg.get("premium") is None:
            # compute theoretical at t0
            m = bs_option(spot, leg["strike"], rate_pct, days_to_expiry, iv_pct, contract=leg["type"])
            leg["premium"] = m["price"]
            print(f"Leg {leg['type']} K={leg['strike']} premium set to BS theoretical = {leg['premium']:.2f}")

    initial_cost = compute_initial_cost(legs)
    print(f"\nInitial cost of strategy (positive = net debit paid): {initial_cost:.2f} (BUY=pay, SELL=receive)")

    # Build spot grid and days slices
    spot_range = np.arange(spot * 0.8, spot * 1.2 + 1, max(1, int(round((spot*0.4)/80))))  # ~80 points across 40% span
    # We'll simulate 4 time slices: t0 (today), mid (half), near expiry (1 day), expiry (0)
    days_slices = sorted(list(set([days_to_expiry, max(1, days_to_expiry//2), 1, 0])))
    # For BS, we must pass at least 1 day to mibian; we'll treat days==0 as expiry (use intrinsic pricing)
    # Evaluate
    results = evaluate_strategy(legs, spot_range, days_slices, rate_pct, iv_pct)

    # Plot PnL curves at the time slices (strategy MTM - initial_cost)
    plt.figure(figsize=(10,6))
    for d in days_slices:
        val = results[d]["value_by_spot"]
        pnl = val - initial_cost
        label = f"{d} days"
        plt.plot(spot_range, pnl, label=label, linewidth=2)
    plt.axhline(0, color='k', linewidth=0.7)
    plt.title("Strategy PnL vs Spot at different times to expiry")
    plt.xlabel("Spot Price")
    plt.ylabel("PnL (INR)")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Greeks (Delta, Theta, Vega) for some selected days (t0 and mid)
    for greek in ("delta_by_spot","theta_by_spot","vega_by_spot"):
        plt.figure(figsize=(10,4))
        for d in [days_slices[0], days_slices[-2] if len(days_slices)>1 else days_slices[0]]:
            arr = results[d][greek]
            label = f"{d} days"
            plt.plot(spot_range, arr, label=label)
        plt.title(greek.replace("_"," ").title())
        plt.xlabel("Spot")
        plt.ylabel(greek.split("_")[0].title())
        plt.legend()
        plt.grid(True)
        plt.show()

    # Expiry analysis (use the last element days=0 if present, else smallest days)
    expiry_days = 0 if 0 in days_slices else min(days_slices)
    expiry_val = results[expiry_days]["value_by_spot"]
    pnl_expiry, max_profit, max_loss, be_points = analyze_expiry(spot_range, expiry_val, initial_cost)

    print("\n--- Expiry analysis ---")
    print(f"Max Profit: {max_profit:.2f}")
    print(f"Max Loss: {max_loss:.2f}")
    print(f"Breakeven points: {be_points if be_points else 'None'}")

    # Show payoff at expiry
    plt.figure(figsize=(10,5))
    plt.plot(spot_range, pnl_expiry, linewidth=2)
    plt.axhline(0, color='k', linewidth=0.7)
    plt.title("Strategy PnL at Expiry")
    plt.xlabel("Spot at Expiry")
    plt.ylabel("PnL (INR)")
    plt.grid(True)
    plt.show()

    # Print leg-by-leg summary (initial vs last)
    print("\nLegs summary (initial premiums used):")
    for leg in legs:
        print(leg)

    # Optionally export results to CSV
    export = input("Export expiry payoff table to CSV? (y/n): ").strip().lower() == "y"
    if export:
        df_out = pd.DataFrame({"Spot": spot_range, "Expiry_MTM": expiry_val, "Expiry_PnL": pnl_expiry})
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"strategy_payoff_{ts}.csv"
        df_out.to_csv(fname, index=False)
        print("Exported to", fname)

if __name__ == "__main__":
    run_cli()
