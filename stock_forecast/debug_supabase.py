import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

print(f"\n🔍 Supabase Connection Debug\n")
print(f"URL: {SUPABASE_URL[:50]}...")
print(f"Key: {SUPABASE_API_KEY[:20]}...")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    print("❌ Missing Supabase credentials")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# Test 1: Check if table exists
print(f"\n1️⃣ Checking if forecast_stocks table exists...")
try:
    response = supabase.table("forecast_stocks").select("*").limit(1).execute()
    print(f"✅ Table exists and is accessible")
except Exception as e:
    print(f"❌ Error accessing table: {str(e)[:100]}")
    exit(1)

# Test 2: Count total records
print(f"\n2️⃣ Counting total records...")
try:
    response = supabase.table("forecast_stocks").select("id").execute()
    count = len(response.data) if response.data else 0
    print(f"✅ Total records: {count}")
except Exception as e:
    print(f"❌ Error counting records: {str(e)[:100]}")

# Test 3: Get sample records
print(f"\n3️⃣ Fetching sample records...")
try:
    response = supabase.table("forecast_stocks").select("*").limit(5).execute()
    if response.data:
        df = pd.DataFrame(response.data)
        print(f"✅ Found {len(df)} records")
        print("\nSample data:")
        print(df.head().to_string())
    else:
        print("❌ No records found")
except Exception as e:
    print(f"❌ Error fetching records: {str(e)[:100]}")

# Test 4: Check RLS policies
print(f"\n4️⃣ Checking table structure and RLS...")
try:
    response = supabase.table("forecast_stocks").select("*").limit(0).execute()
    print(f"✅ Table is readable")
    
    # Try to get column info
    if hasattr(response, 'schema'):
        print(f"Schema: {response.schema}")
except Exception as e:
    print(f"⚠️ Note: {str(e)[:100]}")

# Test 5: List all tables
print(f"\n5️⃣ Listing all available tables...")
try:
    # This requires a direct query - let's try RPC or direct SQL
    response = supabase.rpc("get_tables", {}).execute()
    print(f"Tables: {response}")
except:
    print("ℹ️ Could not list tables (RPC not available)")

print("\n" + "="*60)
print("✨ Debug complete!")
print("="*60)
