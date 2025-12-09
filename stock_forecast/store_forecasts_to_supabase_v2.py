"""
Store forecast data to Supabase
Improved version with proper date handling and RLS-friendly inserts
"""

import os
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import sys

load_dotenv()

# ============= Supabase Config =============
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    raise EnvironmentError("Missing SUPABASE_URL or SUPABASE_API_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# ============= Table Configuration =============
TABLE_NAME = "forecast_stocks"

# ============= Insert Forecast Data =============
def insert_forecast_data(forecast_df: pd.DataFrame, method: str, batch_size: int = 50):
    """
    Insert forecast data into Supabase table with proper date handling
    
    Args:
        forecast_df: DataFrame with forecast data
        method: Forecasting method name (linear, moving_average, arima, prophet)
        batch_size: Number of records to insert per batch
    
    Returns:
        Number of records inserted
    """
    if forecast_df.empty:
        print(f"⚠️ Empty dataframe for method: {method}")
        return 0
    
    try:
        # Prepare data for insertion
        records = []
        
        for _, row in forecast_df.iterrows():
            # Get the actual forecast date from the timestamp column
            forecast_date = pd.to_datetime(row["timestamp"]).date()
            
            record = {
                "forecast_date": forecast_date.isoformat(),
                "symbol": str(row["symbol"]).strip(),
                "method": method,
                "predicted_close": float(row["predicted_close"]),
                "price_change": float(row["price_change"]) if "price_change" in row and pd.notna(row.get("price_change")) else None,
                "price_change_pct": float(row["price_change_pct"]) if "price_change_pct" in row and pd.notna(row.get("price_change_pct")) else None,
                "forecast_day": int(row["forecast_day"]) if "forecast_day" in row and pd.notna(row.get("forecast_day")) else None,
            }
            records.append(record)
        
        # Insert in batches
        total_inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            try:
                response = supabase.table(TABLE_NAME).insert(batch).execute()
                total_inserted += len(batch)
                print(f"   ✅ Inserted batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as e:
                error_str = str(e).lower()
                if "duplicate" in error_str or "unique" in error_str:
                    print(f"   ℹ️ Batch {i//batch_size + 1}: Some records already exist (skipped)")
                    total_inserted += len(batch)
                else:
                    print(f"   ❌ Error inserting batch {i//batch_size + 1}: {str(e)[:100]}")
        
        return total_inserted
    
    except Exception as e:
        print(f"❌ Error processing forecast data: {e}")
        return 0

# ============= Load and Store All Forecasts =============
def store_all_forecasts():
    """Load all forecast CSV files and store them in Supabase"""
    print("\n" + "=" * 70)
    print("🚀 STORING FORECASTS TO SUPABASE")
    print("=" * 70)
    
    # Methods to process
    methods = ["linear", "moving_average", "arima", "prophet"]
    
    total_records = 0
    
    for method in methods:
        file_path = f"forecast_all_stocks_{method}.csv"
        
        if not os.path.exists(file_path):
            print(f"\n⚠️ File not found: {file_path}")
            continue
        
        try:
            print(f"\n📂 Processing: {file_path}")
            
            # Load forecast data
            forecast_df = pd.read_csv(file_path)
            print(f"   Loaded {len(forecast_df)} records")
            
            # Insert into Supabase
            inserted = insert_forecast_data(forecast_df, method)
            total_records += inserted
            
        except Exception as e:
            print(f"❌ Error processing {method}: {e}")
    
    print("\n" + "=" * 70)
    print(f"✨ STORAGE COMPLETED")
    print(f"   Total records stored: {total_records}")
    print("=" * 70)

# ============= Query and Display Forecasts =============
def display_stored_forecasts():
    """Display a summary of stored forecasts"""
    print("\n" + "=" * 70)
    print("📊 STORED FORECASTS SUMMARY")
    print("=" * 70)
    
    try:
        # Get all forecasts
        response = supabase.table(TABLE_NAME).select("*").execute()
        
        if not response.data or len(response.data) == 0:
            print("\n❌ No forecasts found in Supabase")
            return
        
        df = pd.DataFrame(response.data)
        
        print(f"\n✅ Total records: {len(df)}")
        
        # Summary by method
        print("\n📈 By Method:")
        method_summary = df.groupby("method").size()
        for method, count in method_summary.items():
            print(f"   {method:20} {count:5} records")
        
        # Summary by symbol
        print("\n📊 By Symbol:")
        symbol_summary = df.groupby("symbol").size()
        for symbol, count in symbol_summary.items():
            print(f"   {symbol:20} {count:5} records")
        
        # Date range
        print(f"\n📅 Date Range:")
        df['forecast_date'] = pd.to_datetime(df['forecast_date'])
        print(f"   From: {df['forecast_date'].min().date()}")
        print(f"   To:   {df['forecast_date'].max().date()}")
        
        # Sample data
        print("\n📋 Sample Records:")
        sample = df[['forecast_date', 'symbol', 'method', 'predicted_close', 'price_change_pct']].head(10)
        print(sample.to_string(index=False))
        
    except Exception as e:
        print(f"❌ Error displaying forecasts: {e}")

def query_forecasts(symbol=None, method=None):
    """
    Query forecasts with optional filters
    
    Args:
        symbol: Filter by stock symbol (optional)
        method: Filter by forecasting method (optional)
    
    Returns:
        DataFrame with filtered results
    """
    try:
        query = supabase.table(TABLE_NAME).select("*")
        
        if symbol:
            query = query.eq("symbol", symbol)
        if method:
            query = query.eq("method", method)
        
        response = query.execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
    
    except Exception as e:
        print(f"❌ Error querying forecasts: {e}")
        return pd.DataFrame()

# ============= Clear Old Forecasts =============
def clear_old_forecasts(days: int = 30):
    """Delete forecasts older than specified days"""
    print(f"\n🗑️  Clearing forecasts older than {days} days...")
    
    try:
        # Calculate cutoff date
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        response = supabase.table(TABLE_NAME).delete().lt("forecast_date", cutoff_date).execute()
        
        print(f"✅ Deleted {len(response.data) if response.data else 0} old records")
    
    except Exception as e:
        print(f"❌ Error clearing forecasts: {e}")

# ============= Main =============
if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "store":
            store_all_forecasts()
        elif command == "query":
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            method = sys.argv[3] if len(sys.argv) > 3 else None
            results = query_forecasts(symbol=symbol, method=method)
            if not results.empty:
                print("\n" + results.to_string())
            else:
                print("❌ No results found")
        elif command == "display":
            display_stored_forecasts()
        elif command == "clear":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            clear_old_forecasts(days)
        else:
            print(f"❌ Unknown command: {command}")
            print_help()
    else:
        # Default: store and display
        store_all_forecasts()
        display_stored_forecasts()

def print_help():
    """Print usage instructions"""
    help_text = """
    Usage: python3 store_forecasts_to_supabase_v2.py [command] [args]
    
    Commands:
        store                          Store all forecast CSV files to Supabase
        query [symbol] [method]        Query forecasts (optional filters)
        display                        Display summary of stored forecasts
        clear [days]                   Delete forecasts older than N days (default 30)
        
    Examples:
        python3 store_forecasts_to_supabase_v2.py store
        python3 store_forecasts_to_supabase_v2.py query AAPL linear
        python3 store_forecasts_to_supabase_v2.py display
    """
    print(help_text)
