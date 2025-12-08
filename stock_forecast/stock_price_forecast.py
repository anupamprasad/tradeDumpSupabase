import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
import warnings

# Advanced forecasting imports
try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    print("⚠️ statsmodels not installed. ARIMA forecasting unavailable.")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️ prophet not installed. Prophet forecasting unavailable.")

warnings.filterwarnings('ignore')

load_dotenv()

# ============= Supabase Config =============
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("Missing SUPABASE_URL or SUPABASE_API_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============= Fetch Historical Data =============
def fetch_historical_data(symbol: str, days: int = 90) -> pd.DataFrame:
    """Fetch historical stock price data from Supabase"""
    try:
        response = supabase.table("stock_prices").select("*").eq("symbol", symbol).execute()
        
        if not response.data:
            print(f"⚠ No data found for {symbol}")
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        
        # Convert timestamp to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Sort by timestamp and keep last N days
        df = df.sort_values("timestamp").tail(days)
        
        return df
    
    except Exception as e:
        print(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# ============= Forecast Using Linear Regression =============
def forecast_linear_regression(df: pd.DataFrame, symbol: str, days: int = 7) -> pd.DataFrame:
    """
    Forecast stock prices using Linear Regression
    Uses historical close prices to predict next 7 days
    """
    if df.empty or len(df) < 5:
        print(f"⚠ Insufficient data for {symbol} (need at least 5 data points)")
        return pd.DataFrame()
    
    try:
        # Prepare data
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        # Use close price
        prices = df["close"].values.reshape(-1, 1)
        
        # Create feature matrix (X = day number, y = price)
        X = np.arange(len(prices)).reshape(-1, 1)
        y = prices.flatten()
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate future days
        last_date = df["timestamp"].iloc[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(days)]
        future_X = np.arange(len(prices), len(prices) + days).reshape(-1, 1)
        
        # Predict
        predicted_prices = model.predict(future_X)
        
        # Create forecast dataframe
        forecast_df = pd.DataFrame({
            "timestamp": future_dates,
            "symbol": symbol,
            "predicted_close": predicted_prices,
            "forecast_day": [i+1 for i in range(days)]
        })
        
        # Add confidence metrics
        last_price = y[-1]
        forecast_df["price_change"] = forecast_df["predicted_close"] - last_price
        forecast_df["price_change_pct"] = (forecast_df["price_change"] / last_price) * 100
        
        return forecast_df
    
    except Exception as e:
        print(f"❌ Error forecasting {symbol}: {e}")
        return pd.DataFrame()

# ============= Forecast Using Moving Average =============
def forecast_moving_average(df: pd.DataFrame, symbol: str, days: int = 7) -> pd.DataFrame:
    """
    Forecast using exponential weighted moving average (EWMA)
    Better for capturing recent trends
    """
    if df.empty or len(df) < 5:
        return pd.DataFrame()
    
    try:
        df = df.sort_values("timestamp").reset_index(drop=True)
        prices = df["close"].values
        
        # Calculate EWMA
        ewma = pd.Series(prices).ewm(span=min(20, len(prices)), adjust=False).mean()
        
        # Calculate trend (slope of recent data)
        recent_prices = prices[-min(10, len(prices)):]
        trend = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
        
        # Generate forecasts
        last_date = df["timestamp"].iloc[-1]
        last_price = prices[-1]
        
        forecast_list = []
        for i in range(days):
            future_date = last_date + timedelta(days=i+1)
            predicted_price = last_price + (trend * (i + 1))
            
            forecast_list.append({
                "timestamp": future_date,
                "symbol": symbol,
                "predicted_close": predicted_price,
                "forecast_day": i+1,
                "price_change": predicted_price - last_price,
                "price_change_pct": ((predicted_price - last_price) / last_price) * 100
            })
        
        return pd.DataFrame(forecast_list)
    
    except Exception as e:
        print(f"❌ Error forecasting with MA {symbol}: {e}")
        return pd.DataFrame()

# ============= Forecast Using ARIMA =============
def forecast_arima(df: pd.DataFrame, symbol: str, days: int = 7) -> pd.DataFrame:
    """
    Forecast using ARIMA (AutoRegressive Integrated Moving Average)
    Excellent for time series with trend and seasonality
    """
    if not ARIMA_AVAILABLE:
        print(f"⚠️ ARIMA not available. Install: pip install statsmodels")
        return pd.DataFrame()
    
    if df.empty or len(df) < 15:
        print(f"⚠️ Insufficient data for ARIMA {symbol} (need at least 15 data points)")
        return pd.DataFrame()
    
    try:
        df = df.sort_values("timestamp").reset_index(drop=True)
        prices = df["close"].values
        
        # Fit ARIMA model - using auto parameters
        # ARIMA(1,1,1) is a reasonable default for stock prices
        model = ARIMA(prices, order=(1, 1, 1))
        fitted_model = model.fit()
        
        # Forecast
        forecast_result = fitted_model.get_forecast(steps=days)
        predicted_prices = forecast_result.predicted_mean.values
        conf_int = forecast_result.conf_int(alpha=0.05)
        
        # Create forecast dataframe
        last_date = df["timestamp"].iloc[-1]
        last_price = prices[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(days)]
        
        forecast_df = pd.DataFrame({
            "timestamp": future_dates,
            "symbol": symbol,
            "predicted_close": predicted_prices,
            "forecast_day": [i+1 for i in range(days)],
            "lower_bound": conf_int.iloc[:, 0].values,
            "upper_bound": conf_int.iloc[:, 1].values
        })
        
        forecast_df["price_change"] = forecast_df["predicted_close"] - last_price
        forecast_df["price_change_pct"] = (forecast_df["price_change"] / last_price) * 100
        
        return forecast_df
    
    except Exception as e:
        print(f"❌ Error in ARIMA forecast {symbol}: {e}")
        return pd.DataFrame()

# ============= Forecast Using Prophet =============
def forecast_prophet(df: pd.DataFrame, symbol: str, days: int = 7) -> pd.DataFrame:
    """
    Forecast using Facebook Prophet
    Great for handling seasonality and holiday effects
    """
    if not PROPHET_AVAILABLE:
        print(f"⚠️ Prophet not available. Install: pip install prophet")
        return pd.DataFrame()
    
    if df.empty or len(df) < 10:
        print(f"⚠️ Insufficient data for Prophet {symbol} (need at least 10 data points)")
        return pd.DataFrame()
    
    try:
        df_prophet = df[["timestamp", "close"]].copy()
        df_prophet.columns = ["ds", "y"]
        df_prophet = df_prophet.sort_values("ds")
        
        # Initialize and fit Prophet model
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.95,
            changepoint_prior_scale=0.05
        )
        
        model.fit(df_prophet)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=days, freq='D')
        forecast = model.predict(future)
        
        # Get last N days forecast
        forecast_future = forecast.tail(days).copy()
        
        last_price = df_prophet["y"].iloc[-1]
        
        # Create output dataframe
        forecast_df = pd.DataFrame({
            "timestamp": forecast_future["ds"].values,
            "symbol": symbol,
            "predicted_close": forecast_future["yhat"].values,
            "forecast_day": [i+1 for i in range(days)],
            "lower_bound": forecast_future["yhat_lower"].values,
            "upper_bound": forecast_future["yhat_upper"].values
        })
        
        forecast_df["price_change"] = forecast_df["predicted_close"] - last_price
        forecast_df["price_change_pct"] = (forecast_df["price_change"] / last_price) * 100
        
        return forecast_df
    
    except Exception as e:
        print(f"❌ Error in Prophet forecast {symbol}: {e}")
        return pd.DataFrame()

# ============= Main Forecasting Function =============
def generate_forecast(symbol: str, days: int = 7, method: str = "linear") -> pd.DataFrame:
    """
    Generate price forecast for a given symbol
    
    Args:
        symbol: Stock ticker (e.g., "AAPL", "RELIANCE.NS")
        days: Number of days to forecast (default 7)
        method: Forecasting method - "linear", "moving_average", "arima", or "prophet"
    
    Returns:
        DataFrame with forecast data
    """
    print(f"\n📊 Generating {days}-day forecast for {symbol} using {method}...")
    
    # Fetch historical data
    df = fetch_historical_data(symbol, days=90)
    
    if df.empty:
        return pd.DataFrame()
    
    # Generate forecast based on method
    if method == "linear":
        forecast_df = forecast_linear_regression(df, symbol, days)
    elif method == "moving_average":
        forecast_df = forecast_moving_average(df, symbol, days)
    elif method == "arima":
        forecast_df = forecast_arima(df, symbol, days)
    elif method == "prophet":
        forecast_df = forecast_prophet(df, symbol, days)
    else:
        print(f"❌ Unknown method: {method}. Available: linear, moving_average, arima, prophet")
        return pd.DataFrame()
    
    if not forecast_df.empty:
        print(f"✔ Forecast generated for {symbol} ({method})")
    else:
        print(f"⚠️ Could not generate forecast for {symbol}")
    
    return forecast_df

# ============= Save Forecasts to CSV =============
def save_forecast(forecast_df: pd.DataFrame, symbol: str):
    """Save forecast to CSV file"""
    if forecast_df.empty:
        return
    
    filename = f"forecast_{symbol.replace('.', '_')}.csv"
    forecast_df.to_csv(filename, index=False)
    print(f"✔ Forecast saved to {filename}")

# ============= Main Execution =============
if __name__ == "__main__":
    # Example tickers to forecast
    TICKERS = [
        "RELIANCE.NS",
        "TCS.NS",
        "HDFCBANK.NS",
        "INFY.NS",
        "AAPL",
        "GOOG"
    ]
    
    # Available forecasting methods
    METHODS = ["linear", "moving_average"]
    
    if ARIMA_AVAILABLE:
        METHODS.append("arima")
    
    if PROPHET_AVAILABLE:
        METHODS.append("prophet")
    
    print("=" * 70)
    print("📈 Stock Price Forecast - 7 Days")
    print(f"Available methods: {', '.join(METHODS)}")
    print("=" * 70)
    
    all_forecasts = {}
    
    # Generate forecasts for each method
    for method in METHODS:
        print(f"\n{'='*70}")
        print(f"🔮 FORECASTING WITH {method.upper()}")
        print(f"{'='*70}")
        
        all_forecasts[method] = []
        
        for ticker in TICKERS:
            # Generate forecast
            forecast = generate_forecast(ticker, days=7, method=method)
            
            if not forecast.empty:
                all_forecasts[method].append(forecast)
                save_forecast(forecast, f"{ticker.replace('.', '_')}_{method}")
                
                # Display forecast
                print(f"\n📊 {ticker} - {method.upper()} Forecast:")
                print(forecast[["timestamp", "symbol", "predicted_close", "price_change_pct"]].to_string(index=False))
        
        # Combine all forecasts for this method
        if all_forecasts[method]:
            combined_df = pd.concat(all_forecasts[method], ignore_index=True)
            combined_df.to_csv(f"forecast_all_stocks_{method}.csv", index=False)
            print(f"\n✔ All {method} forecasts saved to forecast_all_stocks_{method}.csv")
    
    print("\n" + "=" * 70)
    print("📊 FORECAST COMPARISON SUMMARY")
    print("=" * 70)
    
    # Create comparison summary
    comparison_data = []
    for method in METHODS:
        if all_forecasts[method]:
            combined_df = pd.concat(all_forecasts[method], ignore_index=True)
            
            for symbol in combined_df["symbol"].unique():
                symbol_data = combined_df[combined_df["symbol"] == symbol]
                avg_price = symbol_data["predicted_close"].mean()
                avg_change = symbol_data["price_change_pct"].mean()
                
                comparison_data.append({
                    "Symbol": symbol,
                    "Method": method.upper(),
                    "Avg Predicted Price": f"{avg_price:.2f}",
                    "Avg % Change": f"{avg_change:.2f}%"
                })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df.to_csv("forecast_comparison.csv", index=False)
        print(comparison_df.to_string(index=False))
        print("\n✔ Comparison saved to forecast_comparison.csv")
    
    print("\n" + "=" * 70)
    print("✨ Forecast generation completed!")
    print("=" * 70)
    
    print("\n📁 Generated Files:")
    print("  - forecast_all_stocks_{method}.csv (for each method)")
    print("  - forecast_{symbol}_{method}.csv (individual forecasts)")
    print("  - forecast_comparison.csv (cross-method comparison)")
