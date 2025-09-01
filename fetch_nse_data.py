import requests
import pandas as pd
import datetime

# ----------------------------
# Function to get NSE index data
# ----------------------------
def get_index_data(symbol="NIFTY", period="1mo", interval="15m"):
    """
    Fetch historical data for NIFTY or BANKNIFTY from NSE.
    
    symbol: "NIFTY" or "BANKNIFTY"
    period: "1d","5d","1mo","3mo","6mo","1y","2y","5y","max"
    interval: "1m","5m","15m","1d","1wk","1mo"
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/%5E{symbol}50"
    params = {
        "range": period,
        "interval": interval,
        "events": "history"
    }
    r = requests.get(url, params=params)
    data = r.json()

    timestamps = data['chart']['result'][0]['timestamp']
    indicators = data['chart']['result'][0]['indicators']['quote'][0]

    df = pd.DataFrame(indicators)
    df['Datetime'] = pd.to_datetime(timestamps, unit='s')
    df = df[['Datetime','open','high','low','close','volume']]
    df.columns = ['Datetime','Open','High','Low','Close','Volume']
    return df

# ----------------------------
# Example Usage
# ----------------------------
if __name__ == "__main__":
    # Fetch 6 months of 15-min BankNifty data
    df = get_index_data(symbol="BANKNIFTY", period="6mo", interval="15m")
    print(df.head())

    # Save to CSV
    today = datetime.date.today().strftime("%Y-%m-%d")
    df.to_csv(f"banknifty_{today}.csv", index=False)
    print(f"Saved data to banknifty_{today}.csv")
