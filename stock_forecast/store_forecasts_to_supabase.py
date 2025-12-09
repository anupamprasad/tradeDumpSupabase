import os
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

# ============= Supabase Config =============
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    raise EnvironmentError("Missing SUPABASE_URL or SUPABASE_API_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# ============= Table Configuration =============
TABLE_NAME = "forecast_stocks"

# ============= Create Table (if not exists) =============
def create_forecast_table():
    """
    Create the forecast_stocks table in Supabase if it doesn't exist.
    This function uses raw SQL to create the table.
    """
    print(f"📝 Creating/checking table '{TABLE_NAME}'...")
    
    try:
        # Check if table exists by trying to query it
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        print(f"✔ Table '{TABLE_NAME}' already exists")
        return True
    except Exception as e:
        print(f"⚠️ Table doesn't exist or error occurred: {str(e)[:100]}")
        print(f"ℹ️ Please create the table manually in Supabase with the following schema:")
        print_table_schema()
        return False

def print_table_schema():
    """Print the recommended table schema"""
    schema = """
    CREATE TABLE forecast_stocks (
        id BIGSERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT NOW(),
        forecast_date DATE NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        method VARCHAR(50) NOT NULL,
        predicted_close DECIMAL(10, 2) NOT NULL,
        price_change DECIMAL(10, 2),
        price_change_pct DECIMAL(5, 2),
        forecast_day INTEGER,
        lower_bound DECIMAL(10, 2),
        upper_bound DECIMAL(10, 2),
        UNIQUE(forecast_date, symbol, method)
    );
    
    CREATE INDEX idx_symbol ON forecast_stocks(symbol);
    CREATE INDEX idx_method ON forecast_stocks(method);
    CREATE INDEX idx_forecast_date ON forecast_stocks(forecast_date);
    """
    print(schema)

# ============= Insert Forecast Data =============
def insert_forecast_data(forecast_df: pd.DataFrame, method: str, batch_size: int = 100):
    """
    Insert forecast data into Supabase table
    
    Args:
        forecast_df: DataFrame with forecast data
        method: Forecasting method name (linear, moving_average, arima, prophet)
        batch_size: Number of records to insert per batch
    """
    if forecast_df.empty:
        print(f"⚠️ Empty dataframe for method: {method}")
        return 0
    
    try:
        # Prepare data for insertion
        records = []
        today = datetime.now().date()
        
        for _, row in forecast_df.iterrows():
            record = {
                "forecast_date": today.isoformat(),
                "symbol": row["symbol"],
                "method": method,
                "predicted_close": float(row["predicted_close"]),
                "price_change": float(row["price_change"]) if "price_change" in row else None,
                "price_change_pct": float(row["price_change_pct"]) if "price_change_pct" in row else None,
                "forecast_day": int(row["forecast_day"]) if "forecast_day" in row else None,
                "lower_bound": float(row["lower_bound"]) if "lower_bound" in row else None,
                "upper_bound": float(row["upper_bound"]) if "upper_bound" in row else None,
            }
            records.append(record)
        
        # Insert in batches
        total_inserted = 0
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            try:
                response = supabase.table(TABLE_NAME).insert(batch).execute()
                total_inserted += len(batch)
                print(f"✔ Inserted {len(batch)} records for {method}")
            except Exception as e:
                # Check if it's a duplicate key error (OK to skip)
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    print(f"ℹ️ Some records already exist for {method} (skipped)")
                    total_inserted += len(batch)
                else:
                    print(f"❌ Error inserting batch: {str(e)[:100]}")
        
        return total_inserted
    
    except Exception as e:
        print(f"❌ Error processing forecast data: {e}")
        return 0

# ============= Load and Store All Forecasts =============
def store_all_forecasts():
    """
    Load all forecast CSV files and store them in Supabase
    """
    print("\n" + "=" * 70)
    print("🚀 STORING FORECASTS TO SUPABASE")
    print("=" * 70)
    
    # Create table if not exists
    create_forecast_table()
    
    # Methods to process
    methods = ["linear", "moving_average", "arima", "prophet"]
    
    total_records = 0
    
    for method in methods:
        file_path = f"forecast_all_stocks_{method}.csv"
        
        if not os.path.exists(file_path):
            print(f"\n⚠️ File not found: {file_path}")
            print(f"   Generate forecasts first: python3 stock_price_forecast.py")
            continue
        
        try:
            print(f"\n📂 Processing: {file_path}")
            
            # Load forecast data
            forecast_df = pd.read_csv(file_path)
            forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"])
            
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

# ============= Query Stored Forecasts =============
def query_forecasts(symbol: str = None, method: str = None, limit: int = 100):
    """
    Query forecasts from Supabase
    
    Args:
        symbol: Filter by stock symbol (optional)
        method: Filter by forecasting method (optional)
        limit: Maximum number of records to return
    """
    try:
        query = supabase.table(TABLE_NAME).select("*")
        
        if symbol:
            query = query.eq("symbol", symbol)
        
        if method:
            query = query.eq("method", method)
        
        response = query.limit(limit).order("forecast_date", desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            return df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        print(f"❌ Error querying forecasts: {e}")
        return pd.DataFrame()

# ============= Display Stored Data =============
def display_stored_forecasts():
    """
    Display summary of stored forecasts
    """
    print("\n" + "=" * 70)
    print("📊 FORECAST DATA IN SUPABASE")
    print("=" * 70)
    
    try:
        # Get all forecasts
        df = query_forecasts(limit=1000)
        
        if df.empty:
            print("No forecasts found in Supabase")
            return
        
        print(f"\n📈 Total records: {len(df)}")
        
        # Summary by method
        print("\n📋 Summary by Forecasting Method:")
        method_summary = df.groupby("method").size()
        print(method_summary)
        
        # Summary by symbol
        print("\n📋 Summary by Stock Symbol:")
        symbol_summary = df.groupby("symbol").size()
        print(symbol_summary)
        
        # Latest forecasts
        print("\n📅 Latest Forecasts (Sample):")
        latest = df.head(10)[["forecast_date", "symbol", "method", "predicted_close", "price_change_pct"]]
        print(latest.to_string(index=False))
        
    except Exception as e:
        print(f"❌ Error displaying forecasts: {e}")

# ============= Clear Old Forecasts =============
def clear_old_forecasts(days: int = 30):
    """
    Delete forecasts older than specified days
    
    Args:
        days: Number of days to keep (default 30)
    """
    from datetime import timedelta
    
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        response = supabase.table(TABLE_NAME).delete().lt("forecast_date", cutoff_date).execute()
        
        print(f"✔ Deleted forecasts older than {days} days")
        
    except Exception as e:
        print(f"❌ Error deleting old forecasts: {e}")

# ============= Main Execution =============
if __name__ == "__main__":
    import sys
    
    print("\n🔍 Stock Forecast Storage Manager")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "store":
            store_all_forecasts()
        elif command == "query":
            symbol = sys.argv[2] if len(sys.argv) > 2 else None
            method = sys.argv[3] if len(sys.argv) > 3 else None
            results = query_forecasts(symbol=symbol, method=method)
            if not results.empty:
                print(results.to_string())
            else:
                print("No results found")
        elif command == "display":
            display_stored_forecasts()
        elif command == "clear":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            clear_old_forecasts(days)
        else:
            print(f"Unknown command: {command}")
            print_help()
    else:
        # Default: store all forecasts and display summary
        store_all_forecasts()
        display_stored_forecasts()

def print_help():
    """Print usage instructions"""
    help_text = """
    Usage: python3 store_forecasts_to_supabase.py [command] [args]
    
    Commands:
        store                          Store all forecast CSV files to Supabase
        query [symbol] [method]        Query forecasts (optional filters)
        display                        Display summary of stored forecasts
        clear [days]                   Delete forecasts older than N days (default 30)
        
    Examples:
        python3 store_forecasts_to_supabase.py store
        python3 store_forecasts_to_supabase.py query AAPL linear
        python3 store_forecasts_to_supabase.py display
        python3 store_forecasts_to_supabase.py clear 14
    """
    print(help_text)
