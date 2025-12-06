import yfinance as yf
import requests
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE")

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def validate_env():
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_API_KEY:
        missing.append("SUPABASE_API_KEY")
    if not SUPABASE_TABLE:
        missing.append("SUPABASE_TABLE")
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

# Folder to store dumped data
DATA_DIR = "daily_stock_data"
os.makedirs(DATA_DIR, exist_ok=True)

TICKERS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "AAPL",
    "GOOG"
]

def insert_to_supabase(rows):
    if not SUPABASE_URL or not SUPABASE_API_KEY or not SUPABASE_TABLE:
        print("❌ Supabase config missing; skipping insert")
        return

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{SUPABASE_TABLE}"
    headers = HEADERS.copy()
    headers.update({
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
    })

    try:
        response = requests.post(url, json=rows, headers=headers, timeout=30)
    except Exception as e:
        print("❌ Supabase network error:", e)
        return

    if response.status_code not in (200, 201):
        print("❌ Supabase Insert Error:", response.status_code, response.text)
    else:
        print("✔ Inserted into Supabase")

def dump_daily_data():
    print("\n=== Running Daily Stock Dump ===")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    all_rows = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period="1d", interval="1d", progress=False)

            if df.empty:
                print(f"⚠ No data for {ticker} today.")
                continue

            filename = os.path.join(DATA_DIR, f"{ticker.replace('.', '_')}.csv")

            # Append if file exists and non-empty, else create new with header
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                df.to_csv(filename, mode='a', header=False)
            else:
                df.to_csv(filename)

            print(f"✔ Dumped CSV: {ticker}")

            # Use the last available row (in case the DataFrame has more than one row)
            ohlc = df.iloc[-1]

            row = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": ticker,
                "open": float(ohlc['Open']),
                "high": float(ohlc['High']),
                "low": float(ohlc['Low']),
                "close": float(ohlc['Close']),
                "volume": float(ohlc['Volume'])
            }

            all_rows.append(row)
            print(f"✔ Prepared row for: {ticker}")

        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")

    if all_rows:
        insert_to_supabase(all_rows)

    print("=== Daily Dump Completed ===\n")

# Scheduler: run daily at 6 PM
scheduler = BlockingScheduler()
scheduler.add_job(dump_daily_data, 'cron', hour=18, minute=0)

if __name__ == "__main__":
    print("Starting Supabase Auto-Dump Scheduler...")
    try:
        validate_env()
    except EnvironmentError as e:
        print(f"Environment error: {e}")
        print("Exiting.")
        raise

    dump_daily_data()  # Run immediately once
    # Only start the long-running scheduler when explicitly enabled.
    # This keeps the script safe to run from cron (one-off) by default.
    if os.getenv("ENABLE_SCHEDULER", "0") == "1":
        scheduler.start()
