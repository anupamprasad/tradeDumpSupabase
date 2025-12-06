import pandas as pd
from datetime import datetime
from supabase import create_client

# Supabase setup
SUPABASE_URL = "https://qcsnicfivondpxcgdzer.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjc25pY2Zpdm9uZHB4Y2dkemVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyMTk5ODAsImV4cCI6MjA3OTc5NTk4MH0.mH2lUVdRPKhTQrQqfULm5QpuEkoIArRDqsUgDmjF1r0"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read CSV
df = pd.read_csv("btc_data.csv")

# Convert ms timestamps to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Convert Timestamp to string
df['timestamp'] = df['timestamp'].apply(lambda x: x.isoformat())

# Prepare records
records = df.to_dict(orient="records")

# Insert
supabase.table("trades_3").insert(records).execute()
