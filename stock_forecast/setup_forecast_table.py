#!/usr/bin/env python3
"""
Setup script to create the forecast_stocks table in Supabase.
Run this once before using the storage module.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    raise EnvironmentError("Missing SUPABASE_URL or SUPABASE_API_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# ============= Create Table via SQL =============
def create_table_via_rpc():
    """
    Create the forecast_stocks table using Supabase RPC if available
    """
    print("🔧 Attempting to create table via SQL...")
    
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS forecast_stocks (
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
        """,
        "CREATE INDEX IF NOT EXISTS idx_symbol ON forecast_stocks(symbol);",
        "CREATE INDEX IF NOT EXISTS idx_method ON forecast_stocks(method);",
        "CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_stocks(forecast_date);"
    ]
    
    try:
        # Try using Supabase REST API with SQL
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # Attempt to execute SQL via REST endpoint
        for sql in sql_commands:
            # This won't work directly - Supabase doesn't expose SQL execution via REST
            # But we can try the RPC approach if a function exists
            pass
        
        print("⚠️ Cannot execute SQL directly via REST API")
        return False
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return False

# ============= Manual Setup Instructions =============
def print_setup_instructions():
    """
    Print step-by-step instructions for manual table creation
    """
    instructions = """
    
    ╔════════════════════════════════════════════════════════════════╗
    ║         FORECAST_STOCKS TABLE SETUP INSTRUCTIONS              ║
    ╚════════════════════════════════════════════════════════════════╝
    
    Follow these steps to create the forecast_stocks table:
    
    1. Go to your Supabase project dashboard:
       https://app.supabase.com
    
    2. Select your project and go to the SQL Editor
    
    3. Click "New Query" or "+" to create a new query
    
    4. Copy and paste the following SQL commands:
    
    ────────────────────────────────────────────────────────────────
    
    -- Create the forecast_stocks table
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
    
    -- Create indexes for better query performance
    CREATE INDEX idx_symbol ON forecast_stocks(symbol);
    CREATE INDEX idx_method ON forecast_stocks(method);
    CREATE INDEX idx_forecast_date ON forecast_stocks(forecast_date);
    
    ────────────────────────────────────────────────────────────────
    
    5. Click "Run" to execute the SQL commands
    
    6. You should see "Success" messages for each command
    
    7. You can now use the storage module:
       python3 store_forecasts_to_supabase.py store
    
    ╔════════════════════════════════════════════════════════════════╗
    ║               TABLE CREATED SUCCESSFULLY! ✓                    ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print(instructions)

# ============= Verify Table Exists =============
def verify_table_exists():
    """
    Check if the forecast_stocks table exists
    """
    print("\n🔍 Verifying table existence...")
    
    try:
        response = supabase.table("forecast_stocks").select("*").limit(1).execute()
        print("✅ Table 'forecast_stocks' exists and is accessible!")
        return True
    except Exception as e:
        if "Could not find the table" in str(e) or "PGRST2" in str(e):
            print("❌ Table 'forecast_stocks' does not exist yet")
            return False
        else:
            print(f"⚠️ Error checking table: {str(e)[:100]}")
            return False

# ============= Main Execution =============
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("📋 FORECAST_STOCKS TABLE SETUP")
    print("=" * 70)
    
    # Check if table already exists
    if verify_table_exists():
        print("\n✨ Table is ready to use!")
        print("You can now run: python3 store_forecasts_to_supabase.py store")
    else:
        print("\n❌ Table needs to be created")
        print_setup_instructions()
        
        print("\n\n⏳ Waiting for manual table creation...")
        print("Once you've created the table in Supabase, run this script again to verify.")
        
        input("\nPress Enter after creating the table to verify...")
        
        if verify_table_exists():
            print("\n✅ Table verified successfully!")
            print("You can now run: python3 store_forecasts_to_supabase.py store")
        else:
            print("\n❌ Table still not found. Please check the Supabase dashboard.")
