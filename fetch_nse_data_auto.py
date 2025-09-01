import requests
import pandas as pd
import datetime

# NSE Option Chain API URLs
NSE_URLS = {
    "NIFTY": "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
    "BANKNIFTY": "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"
}

# Headers (NSE requires a browser-like request)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}

def fetch_option_chain(symbol="NIFTY"):
    """Fetch Option Chain data from NSE (CE + PE)."""
    session = requests.Session()
    url = NSE_URLS[symbol]
    response = session.get(url, headers=HEADERS).json()

    records = []
    for item in response['records']['data']:
        strike = item.get('strikePrice')
        expiry = item.get('expiryDate')

        ce = item.get('CE', {})
        pe = item.get('PE', {})

        records.append({
            "Symbol": symbol,
            "Expiry": expiry,
            "Strike": strike,
            "CE_LTP": ce.get('lastPrice'),
            "CE_OI": ce.get('openInterest'),
            "CE_IV": ce.get('impliedVolatility'),
            "PE_LTP": pe.get('lastPrice'),
            "PE_OI": pe.get('openInterest'),
            "PE_IV": pe.get('impliedVolatility'),
        })

    df = pd.DataFrame(records)
    return df.dropna(subset=["CE_LTP","PE_LTP"])

# ----------------------------
# Example Usage
# ----------------------------
if __name__ == "__main__":
    df = fetch_option_chain("BANKNIFTY")
    print(df.head(20))  # show top strikes
    today = datetime.date.today().strftime("%Y-%m-%d")
    df.to_csv(f"banknifty_option_chain_{today}.csv", index=False)
    print(f"Saved option chain to banknifty_option_chain_{today}.csv")
