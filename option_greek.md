# Option Greeks – The 5 Key Metrics
## 1. Delta (Δ) – Directional sensitivity

Meaning: How much the option price changes if the underlying (NIFTY/BANKNIFTY) moves by 1 point.

**Example:**

NIFTY = 20,000

Call option Delta ≈ 0.5

If NIFTY goes up +100 points, the option price increases by 100 × 0.5 = 50 points.

**Rule of Thumb:**

Calls: Delta between 0 and 1.

Puts: Delta between 0 and -1.

ATM options → Δ ~ 0.5

Deep ITM → Δ ~ 1

Deep OTM → Δ ~ 0

## 2. Gamma (Γ) – Acceleration of Delta

Meaning: How much Delta itself changes if the underlying moves 1 point.

**Example:**

A NIFTY Call has Delta = 0.5, Gamma = 0.002.

If NIFTY goes up 100 points,
New Delta = 0.5 + (100 × 0.002) = 0.7.

Now the option behaves more like the underlying.

Think of Gamma as "steering sensitivity" – higher Gamma means your Delta moves faster.

## 3. Theta (Θ) – Time decay

Meaning: How much the option loses in value each day due to time passing.

**Example:**

A BankNifty option premium = ₹200, Theta = -5.

If the market doesn’t move at all, tomorrow the option is worth ₹195 (₹5 lost just due to time).

**Rule of Thumb:**

Short sellers love Theta (they earn from decay).

Buyers hate Theta (their option bleeds every day).

## 4. Vega (ν) – Volatility sensitivity

Meaning: How much the option price changes if Implied Volatility (IV) changes by 1%.

**Example:**

NIFTY Call = ₹150, Vega = 8.

If IV rises by 5%, option price increases by ₹8 × 5 = ₹40 → new price ₹190.

When events like RBI policy, Elections, or Budget approach → IV rises → options get expensive.

## 5. Rho (ρ) – Interest rate sensitivity

Meaning: Change in option price if interest rate changes by 1%.

**Example:**

NIFTY Call Rho = 0.5.

If interest rate rises by 1%, Call increases by 0.5.

Usually small in Indian markets → traders mostly ignore Rho.

📊 Practical Scenario: BANKNIFTY Weekly Options

Let’s say BankNifty = 45,000, and you buy an ATM 45,000 CE at ₹200. Greeks might look like this:

Greek | Value | Meaning
------|-------|--------
Delta | 0.5	| If BN moves +100, option +50
Gamma | 0.004	| For 100-point move, Delta jumps from 0.5 → 0.9
Theta | -10	| You lose ₹10 per lot per day if price doesn’t move
Vega  | 6	| If IV rises 2%, option gains ₹12
Rho	  | 0.1	| Almost negligible

📊 Summary Table
| Greek | Measures                     | Positive for | Impact before Expiry               |
| ----- | ---------------------------- | ------------ | ---------------------------------- |
| Delta | Price change with stock move | Calls        | ATM ≈ 0.5, ITM → 1, OTM → 0        |
| Gamma | Change in Delta              | Both         | Highest at ATM, spikes near expiry |
| Theta | Time decay per day           | Sellers      | Accelerates near expiry            |
| Vega  | Volatility sensitivity       | Buyers       | Higher for longer expiries         |
| Rho   | Interest rate sensitivity    | Calls        | Minor for short options            |


| Symbol    | Expiry      | Strike | Spot  | CE\_LTP | PE\_LTP | IV\_CE | IV\_PE | Delta\_CE | Delta\_PE | Gamma  | Theta\_CE | Theta\_PE | Vega |
| --------- | ----------- | ------ | ----- | ------- | ------- | ------ | ------ | --------- | --------- | ------ | --------- | --------- | ---- |
| BANKNIFTY | 04-Sep-2025 | 44500  | 44610 | 225.5   | 230.1   | 15.2   | 15.8   | 0.48      | -0.52     | 0.0012 | -15.3     | -14.8     | 22.4 |
| BANKNIFTY | 04-Sep-2025 | 44600  | 44610 | 190.3   | 260.7   | 15.0   | 16.1   | 0.45      | -0.55     | 0.0011 | -14.7     | -15.0     | 21.9 |


## Key Insights
- Delta + Gamma → Directional risk
- Theta → Time decay risk (always hurts buyers)
- Vega → Volatility risk
- Rho → Minor, usually ignored in short-dated trading
- Before expiry: Gamma & Theta dominate.

## 👉 Interpretation:

If BN rallies fast → Delta + Gamma make you profit quickly.
If BN stays sideways → Theta decay eats your premium.
If news increases IV → Vega boosts your option price even without index moving.

## 🏆 Golden Rules for Traders

Intraday traders focus on Delta + Gamma.
Positional sellers rely on Theta (decay works in their favor).
Event traders (Budget, Elections) focus on Vega (IV spikes).
Rho is mostly ignored for NIFTY/BANKNIFTY.

# Visual chart (Delta/Gamma/Theta curves vs strike) to know how Greeks behave before expiry
## CALL Option Greeks
<img width="2379" height="1530" alt="image" src="https://github.com/user-attachments/assets/d35931bc-f057-4350-b1a6-0dc479b3cb18" />

## PUT Option Greeks
<img width="2379" height="1580" alt="image" src="https://github.com/user-attachments/assets/0375b101-eede-4567-aa20-41dc37828161" />

# Put Option Greeks Conceptual Definition
## 📊 Long Put Greeks Exposure (Buyer vs Seller)
| Greek         | Buyer of Put (Long Put)            | Seller of Put (Short Put)          | Interpretation                                                                                          |
| ------------- | ---------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Delta (Δ)** | **Negative** (≈ –0.50 at ATM)      | **Positive** (≈ +0.50 at ATM)      | Buyer gains if underlying falls; seller gains if underlying rises.                                      |
| **Gamma (Γ)** | **Positive** (≈ +0.02)             | **Negative** (≈ –0.02)             | Buyer’s Delta becomes more favorable with bigger moves (convexity). Seller’s Delta worsens (concavity). |
| **Theta (Θ)** | **Negative** (≈ –0.05/day)         | **Positive** (≈ +0.05/day)         | Buyer loses daily to time decay. Seller earns from time decay.                                          |
| **Vega (ν)**  | **Positive** (≈ +0.12 per 1% IV)   | **Negative** (≈ –0.12 per 1% IV)   | Buyer benefits if IV rises (volatility expansion). Seller suffers if IV rises.                          |
| **Rho (ρ)**   | **Negative** (≈ –0.02 per 1% rate) | **Positive** (≈ +0.02 per 1% rate) | Buyer loses slightly if interest rates rise. Seller benefits slightly.                                  |

## Examples:
1️⃣ Buyer (Long Put)
| Spot @ Expiry  | Payoff = max(K – S, 0) | P\&L = Payoff – Premium |
| -------------- | ---------------------- | ----------------------- |
| 90 (fall)      | 10                     | **+6.5 (WIN)**          |
| 95 (mild fall) | 5                      | **+1.5 (WIN)**          |
| 100 (ATM)      | 0                      | **–3.5 (LOSS)**         |
| 105 (rise)     | 0                      | **–3.5 (LOSS)**         |
| 110 (big rise) | 0                      | **–3.5 (LOSS)**         |

👉 Buyer has limited loss (–3.5) but unlimited profit potential as spot falls.

2️⃣ Seller (Short Put)
| Spot @ Expiry  | Obligation = –max(K – S, 0) | P\&L = Premium – Obligation |
| -------------- | --------------------------- | --------------------------- |
| 90 (fall)      | –10                         | **–6.5 (LOSS)**             |
| 95 (mild fall) | –5                          | **–1.5 (LOSS)**             |
| 100 (ATM)      | 0                           | **+3.5 (WIN)**              |
| 105 (rise)     | 0                           | **+3.5 (WIN)**              |
| 110 (big rise) | 0                           | **+3.5 (WIN)**              |

👉 Seller has limited gain (+3.5) but unlimited downside risk if spot crashes.

3️⃣ Effect of Time Decay (Theta)
- 10 days to expiry → Premium ≈ ₹3.50
- 5 days to expiry → Premium ≈ ₹2.20 (loses value fast)
- At expiry → Premium = intrinsic only

For Buyer:
- Waiting hurts if spot doesn’t fall (premium decays).
- Fast move down is needed to win.

For Seller:
- Waiting helps (collects Theta).
- Sideways/rising market is perfect.

4️⃣ Effect of Volatility (Vega)
- At 20% IV → Premium ≈ ₹3.50
- At 30% IV → Premium ≈ ₹5.00

For Buyer:
- Higher IV → Premium costlier, but if already holding → option value rises.

For Seller:
- Higher IV → more risk, mark-to-market loss (must buy back costlier).

✅ Summary Matrix
| Factor        | Long Put (Buyer)     | Short Put (Seller)               |
| ------------- | -------------------- | -------------------------------- |
| Spot ↓ (down) | Big Profits          | Big Losses                       |
| Spot ↑ (up)   | Small Loss (premium) | Small Gain (premium)             |
| Time Decay    | Hurts (–Theta)       | Helps (+Theta)                   |
| Volatility ↑  | Helps (+Vega)        | Hurts (–Vega)                    |
| Max Loss      | Premium Paid (₹3.5)  | Unlimited (huge if spot crashes) |
| Max Gain      | Huge (spot → 0)      | Limited (₹3.5)                   |

📊 ATM Put Greeks & P&L Sensitivity
Assumptions
- Strike = 100
- Spot = 100 initially
- IV = 20%
- Risk-free = 0
- Lot size = 1
- Premium at entry ≈ ₹3.50

We’ll track Delta, Theta, Vega and P&L at different spot levels & days-to-expiry.

1️⃣ 10 Days to Expiry (Fresh Trade)
| Spot | Premium (approx) | Delta | Theta (per day) | Vega  | Buyer P\&L | Seller P\&L |
| ---- | ---------------- | ----- | --------------- | ----- | ---------- | ----------- |
| 90   | 10.20            | –0.85 | –0.25           | +0.20 | +6.7 ✅     | –6.7 ❌      |
| 95   | 5.40             | –0.60 | –0.18           | +0.15 | +1.9 ✅     | –1.9 ❌      |
| 100  | 3.50             | –0.50 | –0.12           | +0.12 | 0          | 0           |
| 105  | 2.20             | –0.30 | –0.08           | +0.08 | –1.3 ❌     | +1.3 ✅      |
| 110  | 1.40             | –0.15 | –0.04           | +0.05 | –2.1 ❌     | +2.1 ✅      |

🔹 Buyer: Needs quick move down (Delta ≈ –0.5, Vega helps).
🔹 Seller: Happy if sideways/up, collects Theta.

2️⃣ 5 Days to Expiry (Theta Accelerates)
| Spot | Premium | Delta | Theta | Vega  | Buyer P\&L | Seller P\&L |
| ---- | ------- | ----- | ----- | ----- | ---------- | ----------- |
| 90   | 10.00   | –0.90 | –0.45 | +0.12 | +6.5 ✅     | –6.5 ❌      |
| 95   | 5.00    | –0.65 | –0.30 | +0.09 | +1.5 ✅     | –1.5 ❌      |
| 100  | 2.20    | –0.50 | –0.25 | +0.07 | –1.3 ❌     | +1.3 ✅      |
| 105  | 0.80    | –0.20 | –0.15 | +0.03 | –2.7 ❌     | +2.7 ✅      |
| 110  | 0.20    | –0.05 | –0.08 | +0.01 | –3.3 ❌     | +3.3 ✅      |

🔹 Time decay really hurts buyer if spot stays flat.
🔹 Seller’s P&L accelerates (Theta crush).

3️⃣ Expiry Day (Only Intrinsic Value Left)
| Spot | Premium | Delta | Theta | Vega | Buyer P\&L | Seller P\&L |
| ---- | ------- | ----- | ----- | ---- | ---------- | ----------- |
| 90   | 10.00   | –1.0  | 0     | 0    | +6.5 ✅     | –6.5 ❌      |
| 95   | 5.00    | –1.0  | 0     | 0    | +1.5 ✅     | –1.5 ❌      |
| 100  | 0.00    | 0     | 0     | 0    | –3.5 ❌     | +3.5 ✅      |
| 105  | 0.00    | 0     | 0     | 0    | –3.5 ❌     | +3.5 ✅      |
| 110  | 0.00    | 0     | 0     | 0    | –3.5 ❌     | +3.5 ✅      |

🔹 Buyer’s time value = 0 → only intrinsic matters.
🔹 Seller wins max premium if spot ≥ strike.


## Key Takeaways

- Delta → moves toward –1 if spot drops ITM, 0 if OTM.
- Theta → explodes near expiry; buyer bleeds if spot doesn’t move.
- Vega → only matters when time > 0; vanishes at expiry.
- Buyer → asymmetric bet: small fixed loss, big potential win.
- Seller → insurance provider: small fixed gain, big potential loss.

<img width="1693" height="1101" alt="image" src="https://github.com/user-attachments/assets/f340e486-fdba-4054-8555-7a083d4bd96b" />

## Practical takeaways for traders

- Long put = negative Delta (benefit from falls), positive Vega (benefit from IV spikes), negative Theta (loses with time).
- Sellers of puts have the opposite exposures: they collect Theta (time decay), are short Vega (hurt by IV rises), and short Delta (hurt if market falls).
- Gamma matters for big moves: buyers of options get convexity (benefit grows faster as the underlying moves), sellers have to manage gamma risk.
- For intraday traders: Delta & Gamma dominate immediate P&L.
- For event trades (earnings, RBI), Vega matters: IV moves can change option prices even with small underlying moves.
- Use Greeks together: e.g., if you buy a put before an event you want: (a) enough Delta/Gamma to profit from expected move, and/or (b) positive Vega if you expect IV to rise. But you must pay Theta.


# Popular Option Strategies:
- Long Straddle
- Short Straddle
- Long Strangle
- Short Strangle
- Bull Call Spread
- Bear Put Spread
- Iron Condor
- Covered Call

Option Instrument | Strike | Price  |  | Option Instrument | Strike | Price  |  | Option Instrument |	Reward | Risk
------------------|--------|--------|--|-------------------|--------|--------|--|-------------------|--------|------
CALL              | 24750  | 217.75 |  |	PUT              | 24700  | 168.00 |  | Buy               | 0.6    | 0.3
CALL              | 24800  | 194.85 |  |	PUT	             | 24750	| 193.00 |  | Sell              | 0.75   | 0.75

|Strategy	         | Instrument | Type | Strike | Price   | Qty | P Margin | Profit    | P Exit	| L Margin | Loss       | SL Exit	| Margin      | Week View | At Support | Support Strike |
|------------------|------------|------|--------|---------|-----|----------|-----------|--------|----------|------------|---------|-------------|-----------|------------| ---------------|
|Bull Put Spread	 | PUT	      | Buy	 | 24700  | 168.00	| 75	| 100.8	   | 7,560.00	 | 294.00	| 50.4	   | 3,780.00	  | 117.60	| 54,140.00	  | Bullish	  |            |                |
|                  | PUT	      | Sell | 24750  | 193.00	| 75	| 144.75   | 10,856.25 | 48.25	| 144.75   | 10,856.25	| 337.75	|             |		        |            |                |														
|Bull Call Spread  | CALL	      | Buy	 | 24750  | 217.75  | 75	| 130.65   | 9,798.75	 | 381.06 | 65.325   | 4,899.38   | 152.43	| 54,366.00	  | Bearish	  |            |                |
|                  | CALL	      | Sell | 24800  | 194.85  | 75  | 146.13   | 10,960.31 | 48.71  | 146.13   | 10,960.31  | 340.99	|             |	          |            |                |														
|Call Back Spread	 | CALL	      | Sell | 24750	| 217.75	| 75  |	130.65   | 12,248.44 | 54.44	| 65.325   | 12,248.44	| 381.06	| 67,037.00	  |	          |            |                |
|                  | CALL	      | Buy	 | 24800	| 194.85	| 150	| 146.13   | 17,536.50 | 340.99	| 146.13   | 8,768.25   |	136.40	|             |        	  |            |                |															
|Call Front Spread | CALL	      | Buy	 | 24750	| 217.75	| 75	| 130.65   | 9,798.75	 | 381.06	| 65.32	   | 4,899.38	  | 152.43  |	2,65,981.00	|	          |            |                |	
|                  | CALL	      | Sell | 24800	| 194.85  | 150 | 146.13   | 21,920.63 | 48.71	| 146.13   | 21,920.63  |	340.99	|             |	          |            |                |																		
|Bear Call Spread  | CALL	      | Sell | 24750	| 217.75	| 75	| 163.31   | 12,248.44 | 54.44	| 163.31   | 12,248.44	| 381.06	| 54,366.00	  |           |            |                |
|                  | CALL	      | Buy	 | 24800	| 194.85	| 75	| 116.91   | 8,768.25	 | 340.99	| 58.45	   | 4,384.13   |	136.40	|             |           |	           |                |																				
|Bear Put Spread	 | PUT	      | Sell | 24700	| 168.00	| 75	| 126	     | 9,450.00	 | 42.00	| 126	     | 9,450.00	  | 294.00	| 54,140.00   |	          |	           |                |
|                  | PUT	      | Buy	 | 24750	| 193.00	| 75	| 115.8    |	8,685.00 | 337.75 | 57.9     | 4,342.50   |	135.10	|             |           |            |                |																		
|Put Back Spread	 | PUT	      | Buy	 | 24700	| 168.00	| 150	| 126	     | 15,120.00 | 294.00 |	126	     | 7,560.00   |	117.60	| 67,037.00	  |	          |            |                |
|                  | PUT	      | Sell | 24750	| 193.00	| 75	| 115.8	   | 10,856.25 | 48.25  |	57.9	   | 10,856.25	| 337.75  |             |	          |            |                |																	
|Put Front Spread  | PUT	      | Sell | 24700	| 168.00	| 150	|	126      | 18,900.00 | 42.00	| 126      | 18,900.00	| 294.00  |	2,55,481.00	|           |            |                |
|                  | PUT	      | Buy	 | 24750	| 193.00	| 75	|	115.80   | 8,685.00	 | 337.75 | 57.9     | 4,342.50	  | 135.10	|             |           |	           |                |		

