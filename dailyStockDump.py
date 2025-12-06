import yfinance as yf
import pandas as pd
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler


# Folder to store dumped data
DATA_DIR = "daily_stock_data"
os.makedirs(DATA_DIR, exist_ok=True)

# List of stocks to dump daily
TICKERS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "AAPL",
    "GOOG"
]

def dump_daily_data():
    print("\n=== Running Daily Stock Dump ===")
    today = datetime.now().strftime("%Y-%m-%d")

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="1d", interval="1d")

            if df.empty:
                print(f"⚠ No data for {ticker} today.")
                continue

            filename = os.path.join(DATA_DIR, f"{ticker.replace('.', '_')}.csv")

            # Append if file exists, else create new
            if os.path.exists(filename):
                df.to_csv(filename, mode='a', header=False)
            else:
                df.to_csv(filename)

            print(f"✔ Dumped: {ticker}")

        except Exception as e:
            print(f"❌ Error dumping {ticker}: {e}")

    print("=== Daily Dump Completed ===\n")


# Scheduler to run daily
scheduler = BlockingScheduler()
scheduler.add_job(dump_daily_data, 'cron', hour=17, minute=00)  # Runs every day at 5:00 PM

if __name__ == "__main__":
    print("Starting scheduler... (runs every hour)")
    dump_daily_data()  # Run immediately once
   #grep CRON /var/log/cron scheduler.start()



