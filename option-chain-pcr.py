import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
import random
import os
import glob

from nsepython import option_chain
from datetime import datetime

# === CONFIG ===
INDEX = "NIFTY"
SPOT = 24750   # Current spot price
RANGE = 500    # +/- range in points
MAX_KEEP_FILES = 2

# Timestamp for this run
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"nifty_option_chain_{timestamp}.xlsx"
OI_PNG = f"option_chain_OI_{timestamp}.png"
ChgOI_PNG = f"option_chain_ChangeOI_{timestamp}.png"
PCR_PNG = f"option_chain_PCR_{timestamp}.png"

# === CLEANUP OLD FILES ===
folder = "./"
files = sorted(glob.glob(os.path.join(folder, "nifty_option_chain_*.xlsx")), key=os.path.getmtime)
for f in files[:-MAX_KEEP_FILES]:
    os.remove(f)
    print(f"Deleted old file: {f}")

png_files = sorted(glob.glob(os.path.join(folder, "option_chain_*.png")), key=os.path.getmtime)
for f in png_files[:-MAX_KEEP_FILES*3]:  # 3 PNG per run
    os.remove(f)
    print(f"Deleted old plot: {f}")

def cleanup_old_files(folder="./", max_keep_files=5):
    """
    Deletes old NSE option-chain Excel and PNG files,
    keeping only the latest `max_keep_files` runs.
    """
    # Excel files
    excel_files = sorted(
        glob.glob(os.path.join(folder, "nifty_option_chain_*.xlsx")),
        key=os.path.getmtime
    )
    for f in excel_files[:-max_keep_files]:
        os.remove(f)
        print(f"Deleted old Excel file: {f}")

    # PNG files (assumes 3 PNGs per run)
    png_files = sorted(
        glob.glob(os.path.join(folder, "option_chain_*.png")),
        key=os.path.getmtime
    )
    for f in png_files[:-max_keep_files*3]:
        os.remove(f)
        print(f"Deleted old plot: {f}")

# === Example calling cleanup_old_files ===
#cleanup_old_files(folder="./", max_keep_files=MAX_KEEP_FILES)


# === Set PANDAS ===
# Set pandas to avoid abbreviating the middle columns with ... while printing DataFrame
# This will print all columns or maximize the window if you don't want to set it.
#pd.set_option('display.max_columns', None)
#pd.set_option('display.width', 200)   # optional, adjust console width

# === NSE Fetch ===
nse_url = f"https://www.nseindia.com/api/option-chain-indices?symbol={INDEX}"
#nse_url = f"https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

session = requests.Session()

# Hit homepage first
session.get("https://www.nseindia.com", headers=headers, timeout=10)

# Retry logic
for attempt in range(5):
    try:
        response = session.get(nse_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            break
        else:
            print(f"Attempt {attempt+1}: Failed with HTTP {response.status_code}, retrying...")
    except Exception as e:
        print(f"Attempt {attempt+1}: Error {e}, retrying...")

    time.sleep(random.uniform(1, 3))  # wait 1-3 seconds before retry

else:
    raise Exception("Failed to fetch data after retries")

records = data["records"]["data"]
# End of fetch section


rows = []
for rec in records:
    strike = rec["strikePrice"]
    if SPOT - RANGE <= strike <= SPOT + RANGE:
        ce = rec.get("CE") or {}  # if CE is None, use empty dict
        pe = rec.get("PE") or {}  # if PE is None, use empty dict

        rows.append({
            "expiryDate": ce.get("expiryDate") or pe.get("expiryDate"),
            "strike": strike,
            "CE_OI": ce.get("openInterest", 0),
            "CE_ChgOI": ce.get("changeinOpenInterest", 0),
            "CE_LTP": ce.get("lastPrice", 0),
            "CE_ChgLTP": ce.get("change", 0),           # <-- added
            "CE_IV": ce.get("impliedVolatility", 0),
            "CE_BidQty": ce.get("bidQty", 0),
            "CE_AskQty": ce.get("askQty", 0),
            "PE_OI": pe.get("openInterest", 0),
            "PE_ChgOI": pe.get("changeinOpenInterest", 0),
            "PE_LTP": pe.get("lastPrice", 0),
            "PE_ChgLTP": pe.get("change", 0),           # <-- added
            "PE_IV": pe.get("impliedVolatility", 0),
            "PE_BidQty": pe.get("bidQty", 0),
            "PE_AskQty": pe.get("askQty", 0)
        })

df = pd.DataFrame(rows).sort_values("strike")
df_full = pd.DataFrame(rows).sort_values(["expiryDate", "strike"])

# === CLASSIFY ===
def classify_option(row):
    if row["strike"] == SPOT:
        return "ATM"
    elif row["strike"] < SPOT:
        return "ITM_Put / OTM_Call"
    else:
        return "OTM_Put / ITM_Call"

df["classification"] = df.apply(classify_option, axis=1)

# === SUMMARY TABLE WITH PCR ===
summary = {}
for cat in ["ATM", "ITM", "OTM"]:
    if cat == "ATM":
        subset = df[df["classification"]=="ATM"]
    elif cat == "ITM":
        # ITM Calls: strike < SPOT, ITM Puts: strike > SPOT
        subset = pd.concat([
            df[(df["strike"] < SPOT)],  # ITM Calls
            df[(df["strike"] > SPOT)]   # ITM Puts
        ])
        # But filter columns separately for totals
        ce_subset = df[df["strike"] < SPOT]  # ITM Calls
        pe_subset = df[df["strike"] > SPOT]  # ITM Puts
    else:  # OTM
        # OTM Calls: strike > SPOT, OTM Puts: strike < SPOT
        ce_subset = df[df["strike"] > SPOT]  # OTM Calls
        pe_subset = df[df["strike"] < SPOT]  # OTM Puts

    if cat == "ATM":
        ce_subset = subset
        pe_subset = subset

    ce_total = ce_subset["CE_OI"].sum()
    ce_chg = ce_subset["CE_ChgOI"].sum()
    pe_total = pe_subset["PE_OI"].sum()
    pe_chg = pe_subset["PE_ChgOI"].sum()

    summary[cat] = {
        "CE_TotalOI": ce_total,
        "CE_ChgOI": ce_chg,
        "PE_TotalOI": pe_total,
        "PE_ChgOI": pe_chg,
        "PCR_OI": round(pe_total/ce_total, 2) if ce_total else None,
        "PCR_ChgOI": round(pe_chg/ce_chg, 2) if ce_chg else None
    }


# === OVERALL PCR ===
total_call_oi = df["CE_OI"].sum()
total_put_oi = df["PE_OI"].sum()
total_call_chg = df["CE_ChgOI"].sum()
total_put_chg = df["PE_ChgOI"].sum()

summary["PCR"] = {
    "CE_TotalOI": total_call_oi,
    "CE_ChgOI": total_call_chg,
    "PE_TotalOI": total_put_oi,
    "PE_ChgOI": total_put_chg,
    "PCR_OI": round(total_put_oi / total_call_oi, 2) if total_call_oi else None,
    "PCR_ChgOI": round(total_put_chg / total_call_chg, 2) if total_call_chg else None
}

# === MAX PAIN ===
df["total_oi"] = df["CE_OI"] + df["PE_OI"]
max_pain_strike = df.loc[df["total_oi"].idxmax(), "strike"]

summary["MaxPain"] = {
    "CE_TotalOI": None,
    "CE_ChgOI": None,
    "PE_TotalOI": None,
    "PE_ChgOI": None,
    "PCR_OI": None,
    "PCR_ChgOI": None,
    "Strike": max_pain_strike
}

final_summary = pd.DataFrame(summary).T

# === SAVE TO EXCEL ===
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    # Table 1 → Full Option Chain
    df_full.to_excel(writer, sheet_name="FullOptionChain", index=False)

    # Table 2 → Option Chain OI
    df.to_excel(writer, sheet_name="OptionChainOI", index=False)

    # Table 3 → Summary (ATM/ITM/OTM PCR etc.)
    final_summary.to_excel(writer, sheet_name="Summary", index=True)

    #final_summary.to_excel(writer, sheet_name="Summary")

print(f"\nData saved to {OUTPUT_FILE}")
print(f"Opening Strike: {SPOT}")
print(f"Max Pain Strike: {max_pain_strike}")


print("\nExcel created with:")
print(" - Table 1: Full Option Chain (Table1_FullOptionChain sheet)")
print(" - Table 2: Option Chain (Table2_OptionChainOI sheet)")
print(" - Table 3: Summary (Table3_Summary sheet)")

# === Also display in console ===
print("\n=== TABLE 1: Full Option Chain Data ===")
print(df_full.head(21))

print("\n=== TABLE 2: Option Chain OI Data ===")
nearest_expiry = df["expiryDate"].unique()[0]  # first expiry
df = df[df["expiryDate"] == nearest_expiry]
print(df[["expiryDate", "strike", "CE_OI", "CE_ChgOI", "PE_OI", "PE_ChgOI", "classification"]].head(21)) # show first 21 rows for preview
#print(df.head(10))  # show first 10 rows for preview

print("\n=== TABLE 3: Option Chain Summary for OI and PCR Data ===")
print(final_summary)

# === PLOTS ===
# OI Plot
plt.figure(figsize=(12,6))
plt.bar(df["strike"]-10, df["CE_OI"], width=20, label="Call OI", alpha=0.6)
plt.bar(df["strike"]+10, df["PE_OI"], width=20, label="Put OI", alpha=0.6)
plt.axvline(SPOT, color="red", linestyle="--", label=f"Spot {SPOT}")
plt.axvline(max_pain_strike, color="green", linestyle="--", label=f"Max Pain {max_pain_strike}")
plt.title(f"{INDEX} Option Chain OI (±{RANGE} range)")
plt.xlabel("Strike Price")
plt.ylabel("Open Interest")
plt.legend()
plt.tight_layout()
plt.savefig(OI_PNG)
plt.show()

# ChgOI Plot
plt.figure(figsize=(12,6))
plt.bar(df["strike"]-10, df["CE_ChgOI"], width=20, label="Call Chg OI", alpha=0.6)
plt.bar(df["strike"]+10, df["PE_ChgOI"], width=20, label="Put Chg OI", alpha=0.6)
plt.axvline(SPOT, color="red", linestyle="--", label=f"Spot {SPOT}")
plt.axvline(max_pain_strike, color="green", linestyle="--", label=f"Max Pain {max_pain_strike}")
plt.title(f"{INDEX} Option Chain Change in OI (±{RANGE} range)")
plt.xlabel("Strike Price")
plt.ylabel("Change in Open Interest")
plt.legend()
plt.tight_layout()
plt.savefig(ChgOI_PNG)
plt.show()

# === PCR Visualization ===
pcr_data = final_summary.loc[["ATM", "ITM", "OTM", "PCR"], ["PCR_OI", "PCR_ChgOI"]]

pcr_data.plot(kind="bar", figsize=(10,6))
plt.axhline(1, color="red", linestyle="--", label="Neutral PCR")
plt.title(f"{INDEX} Put/Call Ratio (PCR) by Category")
plt.ylabel("PCR Value")
plt.legend()
plt.tight_layout()
plt.savefig(PCR_PNG)
plt.show()

print("Plots saved as:", OI_PNG, ChgOI_PNG, PCR_PNG)
