# derivative_market_backtest

# 📂 Folder structure
```markdown
derivative_market_backtest/
│── engine.py
│── README.md
└── snapshots/
    └── sample_snapshot.csv
```

# Derivatives Backtest Toolkit

This is a simple Python backtest engine for intraday option-buying strategies (Nifty/BankNifty).

## Features
- Fetch NSE Option Chain snapshots.
- Backtest ATM CE/PE with stop-loss and 1:2 risk-reward.
- Position sizing (risk % per trade).
- Daily trade limits.

## How to Run

1. Install requirements:
```bash
pip install pandas matplotlib requests
```

2. Run paper trading (snapshot collection) -> Collect live option chain data (paper trading):
```bash
#iters 30 => create 30 csv files with interval 1 mins
python engine.py --mode paper --symbol BANKNIFTY --snapshots ./snapshots --pollsec 60 --iters 30 
```

3. Run backtest on collected snapshots:
```bash
# maxtrades depends upon number of csv files
python3 engine.py --mode backtest --symbol BANKNIFTY --snapshots ./snapshots --side AUTO --sl 0.30 --rr 2.0 --riskpct 0.02 --maxtrades 30
```

Follow the links to know more about 
- [Open Interest](https://github.com/sangramnayak1/derivative_market_backtest/blob/master/OPEN_INTEREST.md)
- [Option Greeks](https://github.com/sangramnayak1/derivative_market_backtest/blob/master/OPTION_GREEKS.md)
