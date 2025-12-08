# Stock Price Forecasting Module

This folder contains scripts for generating 7-day stock price forecasts using multiple advanced methods.

## 📊 Features

- **Multiple Forecasting Methods:**
  - Linear Regression - Simple trend-based forecasting
  - Moving Average (EWMA) - Exponential weighted moving average
  - ARIMA - AutoRegressive Integrated Moving Average (with confidence intervals)
  - Prophet - Facebook's time series forecasting (with seasonality handling)

- **Data Source:** Historical data from Supabase `stock_prices` table
- **Supported Stocks:** RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, AAPL, GOOG
- **Forecast Period:** 7 days ahead

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r forecast_requirements.txt
```

### 2. Required Environment Variables

Ensure your `.env` file contains:
```
SUPABASE_URL=your_supabase_url
SUPABASE_API_KEY=your_api_key
```

## 🎯 Usage

Run the forecast script:

```bash
python3 stock_price_forecast.py
```

## 📁 Output Files

The script generates the following files:

- `forecast_all_stocks_linear.csv` - All stocks forecasted with Linear Regression
- `forecast_all_stocks_moving_average.csv` - All stocks forecasted with Moving Average
- `forecast_all_stocks_arima.csv` - All stocks forecasted with ARIMA (if installed)
- `forecast_all_stocks_prophet.csv` - All stocks forecasted with Prophet (if installed)
- `forecast_{symbol}_{method}.csv` - Individual forecast files per stock and method
- `forecast_comparison.csv` - Comparison of all methods across all stocks

## 🔧 Method Details

### Linear Regression
- Simple trend-based prediction
- Assumes linear price movement
- No confidence intervals
- **Best for:** Short-term trends without seasonality

### Moving Average (EWMA)
- Exponential weighted moving average
- Captures recent trend momentum
- Smooths out short-term volatility
- **Best for:** Momentum-based trading strategies

### ARIMA
- **Requires:** `pip install statsmodels`
- Handles trend and seasonality
- Provides 95% confidence intervals (upper_bound, lower_bound)
- More robust for time series with autocorrelation
- **Best for:** Stocks with clear seasonal patterns

### Prophet
- **Requires:** `pip install prophet`
- Handles trends, seasonality, and holiday effects
- Robust to outliers and missing data
- Provides 95% confidence intervals
- **Best for:** Long-term forecasting with complex patterns

## 📊 Output Columns

All forecast files include:

| Column | Description |
|--------|-------------|
| timestamp | Forecast date |
| symbol | Stock ticker |
| predicted_close | Predicted closing price |
| forecast_day | Day number (1-7) |
| price_change | Absolute price change from current |
| price_change_pct | Percentage price change |
| lower_bound* | Lower 95% confidence interval (ARIMA/Prophet only) |
| upper_bound* | Upper 95% confidence interval (ARIMA/Prophet only) |

*Only available for ARIMA and Prophet methods

## 💡 Tips

1. **Compare Methods:** Check `forecast_comparison.csv` to see which method predicts the largest/smallest changes
2. **Confidence Intervals:** Use ARIMA or Prophet for more reliable uncertainty estimates
3. **Data Quality:** Ensure historical data (at least 10-15 days) exists in Supabase for accurate forecasts
4. **Weekly Patterns:** Prophet is best for detecting weekly seasonality in stock prices

## 🐛 Troubleshooting

**ARIMA not available:**
```bash
pip install statsmodels
```

**Prophet not available:**
```bash
pip install prophet
```

If either library is missing, the script will still run with available methods.

## 📝 Notes

- Forecasts are based purely on historical price patterns
- Past performance does not guarantee future results
- Use forecasts as a supplementary tool, not primary trading signal
- Consider market events and external factors for complete analysis
