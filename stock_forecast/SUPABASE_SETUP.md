# 📋 Supabase Table Setup Guide

## Creating the `forecast_stocks` Table

The forecast storage module requires a `forecast_stocks` table in Supabase. Follow these steps:

### Step 1: Access Supabase SQL Editor

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Select your project
3. Click **"SQL Editor"** in the left sidebar
4. Click **"New Query"** or the **"+"** button

### Step 2: Copy & Paste the SQL

Copy and paste this SQL into the editor:

```sql
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
```

### Step 3: Execute the SQL

1. Click the **"Run"** button (or press `Ctrl+Enter`)
2. You should see "Success" messages for each command
3. The table is now created!

### Step 4: Verify the Table

You can verify the table was created by:

1. Going to **"Table Editor"** in the left sidebar
2. You should see `forecast_stocks` in the list of tables

### Step 5: Store Your Forecasts

Once the table is created, run:

```bash
cd stock_forecast
python3 store_forecasts_to_supabase.py store
```

## Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| **id** | BIGSERIAL | Primary key, auto-incremented |
| **created_at** | TIMESTAMP | When the record was inserted |
| **forecast_date** | DATE | Date of the forecast generation |
| **symbol** | VARCHAR(20) | Stock ticker (e.g., AAPL, RELIANCE.NS) |
| **method** | VARCHAR(50) | Forecasting method (linear, moving_average, arima, prophet) |
| **predicted_close** | DECIMAL | Predicted closing price |
| **price_change** | DECIMAL | Absolute price change from current |
| **price_change_pct** | DECIMAL | Percentage price change |
| **forecast_day** | INTEGER | Day number (1-7) |
| **lower_bound** | DECIMAL | 95% confidence lower bound (ARIMA/Prophet) |
| **upper_bound** | DECIMAL | 95% confidence upper bound (ARIMA/Prophet) |

## Troubleshooting

### Error: "Could not find the table 'public.forecast_stocks'"

**Solution:** The table hasn't been created yet. Follow the steps above to create it.

### Error: "Unique constraint violation"

**Solution:** Try again tomorrow. The UNIQUE constraint prevents duplicate forecasts for the same date/symbol/method combination.

### Access Denied

**Solution:** Make sure your Supabase API key has table creation permissions. Check the RLS (Row Level Security) policies.

## Next Steps

After creating the table:

1. Generate forecasts: `python3 stock_price_forecast.py`
2. Store in Supabase: `python3 store_forecasts_to_supabase.py store`
3. Query forecasts: `python3 store_forecasts_to_supabase.py query AAPL linear`
4. View summary: `python3 store_forecasts_to_supabase.py display`
