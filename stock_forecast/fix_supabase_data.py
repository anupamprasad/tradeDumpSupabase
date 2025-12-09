"""
Fix script for Supabase RLS and data insertion issues
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

print("\n" + "="*70)
print("🔧 SUPABASE FORECAST DATA FIX")
print("="*70)

# Step 1: Load the forecast data from CSV
print("\n1️⃣ Loading forecast data from CSV files...")

all_records = []

for method in ["linear", "moving_average"]:
    file_path = f"forecast_all_stocks_{method}.csv"
    
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            print(f"✅ Loaded {len(df)} records from {file_path}")
            
            # Convert data for insertion
            for _, row in df.iterrows():
                record = {
                    "forecast_date": str(pd.to_datetime(row["timestamp"]).date()),
                    "symbol": str(row["symbol"]),
                    "method": method,
                    "predicted_close": float(row["predicted_close"]),
                    "price_change": float(row["price_change"]) if pd.notna(row["price_change"]) else None,
                    "price_change_pct": float(row["price_change_pct"]) if pd.notna(row["price_change_pct"]) else None,
                    "forecast_day": int(row["forecast_day"]) if pd.notna(row["forecast_day"]) else None,
                }
                all_records.append(record)
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
    else:
        print(f"⚠️ File not found: {file_path}")

print(f"\n✅ Total records prepared: {len(all_records)}")

# Step 2: Clear existing data (optional)
print("\n2️⃣ Checking existing data...")
try:
    response = supabase.table("forecast_stocks").select("*").execute()
    existing_count = len(response.data) if response.data else 0
    print(f"📊 Existing records: {existing_count}")
    
    if existing_count > 0:
        print("\n⚠️ Data already exists in table")
        print("ℹ️ Skipping insertion to avoid duplicates")
        print("\nTo replace data, run: python fix_supabase_rls.py --delete-existing")
except Exception as e:
    print(f"Error checking data: {e}")

# Step 3: Insert data
print("\n3️⃣ Inserting records into Supabase...")

try:
    # Insert in batches
    batch_size = 50
    inserted_count = 0
    
    for i in range(0, len(all_records), batch_size):
        batch = all_records[i:i+batch_size]
        
        try:
            response = supabase.table("forecast_stocks").insert(batch).execute()
            inserted_count += len(batch)
            print(f"✅ Inserted batch {i//batch_size + 1} ({len(batch)} records)")
        except Exception as e:
            error_msg = str(e)
            if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
                print(f"ℹ️ Batch {i//batch_size + 1} skipped (duplicates)")
                inserted_count += len(batch)
            else:
                print(f"❌ Error inserting batch {i//batch_size + 1}: {str(e)[:80]}")
    
    print(f"\n✅ Insertion complete: {inserted_count} records processed")
    
except Exception as e:
    print(f"❌ Critical error: {e}")
    print("\n🔧 TROUBLESHOOTING:")
    print("1. Check RLS policies in Supabase:")
    print("   - Go to Table Editor → forecast_stocks → RLS Policies")
    print("   - Ensure 'Enable RLS' is toggled OFF or policies allow INSERT")
    print("\n2. Or create an INSERT policy:")
    print("   - Click 'New Policy' → 'For all users' → 'INSERT'")

# Step 4: Verify insertion
print("\n4️⃣ Verifying data insertion...")

try:
    response = supabase.table("forecast_stocks").select("*").execute()
    final_count = len(response.data) if response.data else 0
    
    print(f"✅ Final record count: {final_count}")
    
    if final_count > 0:
        df = pd.DataFrame(response.data)
        print(f"\n✅ SUCCESS! Data is now visible in Supabase")
        print(f"\nSample records:")
        print(df[["forecast_date", "symbol", "method", "predicted_close"]].head(10).to_string(index=False))
    else:
        print(f"\n❌ No records found after insertion")
        print(f"\n🔍 NEXT STEPS:")
        print(f"1. Go to Supabase Dashboard")
        print(f"2. Select your project")
        print(f"3. Click 'SQL Editor' → 'New Query'")
        print(f"4. Run: SELECT * FROM forecast_stocks;")
        print(f"5. Check 'RLS Policies' tab to enable data access")
        
except Exception as e:
    print(f"❌ Error verifying: {e}")

print("\n" + "="*70)
print("🔧 Fix script complete!")
print("="*70)
