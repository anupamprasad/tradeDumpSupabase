import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import warnings

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
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        df = df.sort_values("timestamp").tail(days)
        
        return df
    
    except Exception as e:
        print(f"❌ Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# ============= Visualization: Historical + Forecast =============
def plot_forecast_vs_historical(historical_df: pd.DataFrame, forecast_df: pd.DataFrame, symbol: str, method: str):
    """
    Create an interactive chart comparing historical prices with forecast
    """
    if historical_df.empty or forecast_df.empty:
        return None
    
    try:
        historical_df = historical_df.sort_values("timestamp")
        forecast_df = forecast_df.sort_values("timestamp")
        
        fig = go.Figure()
        
        # Historical prices
        fig.add_trace(go.Scatter(
            x=historical_df["timestamp"],
            y=historical_df["close"],
            name="Historical Price",
            mode="lines",
            line=dict(color="blue", width=2),
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>"
        ))
        
        # Forecasted prices
        fig.add_trace(go.Scatter(
            x=forecast_df["timestamp"],
            y=forecast_df["predicted_close"],
            name=f"Forecast ({method})",
            mode="lines+markers",
            line=dict(color="red", width=2, dash="dash"),
            marker=dict(size=8),
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Predicted:</b> ₹%{y:.2f}<extra></extra>"
        ))
        
        # Add confidence intervals if available
        if "upper_bound" in forecast_df.columns and "lower_bound" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df["timestamp"],
                y=forecast_df["upper_bound"],
                fill=None,
                mode="lines",
                line_color="rgba(0,0,0,0)",
                showlegend=False,
                name="Upper Bound",
                hoverinfo="skip"
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_df["timestamp"],
                y=forecast_df["lower_bound"],
                fill="tonexty",
                mode="lines",
                line_color="rgba(0,0,0,0)",
                name="95% Confidence Interval",
                fillcolor="rgba(255, 0, 0, 0.1)",
                hoverinfo="skip"
            ))
        
        # Update layout
        fig.update_layout(
            title=f"<b>{symbol} - Price Forecast ({method})</b>",
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            hovermode="x unified",
            height=500,
            template="plotly_white",
            font=dict(size=12)
        )
        
        fig.update_xaxes(rangeslider_visible=False)
        
        return fig
    
    except Exception as e:
        print(f"❌ Error plotting forecast for {symbol}: {e}")
        return None

# ============= Visualization: Multi-Method Comparison =============
def plot_multi_method_comparison(symbol: str, forecast_files: list):
    """
    Compare forecasts from multiple methods on the same chart
    """
    try:
        fig = go.Figure()
        
        # Color map for methods
        colors = {
            "linear": "#1f77b4",
            "moving_average": "#ff7f0e",
            "arima": "#2ca02c",
            "prophet": "#d62728"
        }
        
        # Load and plot each forecast
        for method, file_path in forecast_files:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                df = df[df["symbol"] == symbol].sort_values("timestamp")
                
                if not df.empty:
                    fig.add_trace(go.Scatter(
                        x=df["timestamp"],
                        y=df["predicted_close"],
                        name=method.upper(),
                        mode="lines+markers",
                        line=dict(color=colors.get(method, "#000000"), width=2),
                        marker=dict(size=6),
                        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>"
                    ))
        
        fig.update_layout(
            title=f"<b>{symbol} - Multi-Method Forecast Comparison</b>",
            xaxis_title="Date",
            yaxis_title="Predicted Price (₹)",
            hovermode="x unified",
            height=500,
            template="plotly_white",
            font=dict(size=12)
        )
        
        return fig
    
    except Exception as e:
        print(f"❌ Error creating comparison plot: {e}")
        return None

# ============= Visualization: Price Change Comparison =============
def plot_price_change_comparison(forecast_df: pd.DataFrame, symbol: str, method: str):
    """
    Visualize predicted price changes across forecast period
    """
    if forecast_df.empty:
        return None
    
    try:
        forecast_df = forecast_df.sort_values("forecast_day")
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f"{symbol} - Predicted Price by Day ({method})",
                f"{symbol} - Predicted Price Change by Day ({method})"
            ),
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # Price trend
        fig.add_trace(
            go.Scatter(
                x=forecast_df["forecast_day"],
                y=forecast_df["predicted_close"],
                name="Predicted Price",
                mode="lines+markers",
                line=dict(color="blue", width=2),
                marker=dict(size=10),
                hovertemplate="<b>Day:</b> %{x}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Price change
        colors = ["green" if x >= 0 else "red" for x in forecast_df["price_change_pct"]]
        fig.add_trace(
            go.Bar(
                x=forecast_df["forecast_day"],
                y=forecast_df["price_change_pct"],
                name="% Change",
                marker=dict(color=colors),
                hovertemplate="<b>Day:</b> %{x}<br><b>Change:</b> %{y:.2f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Forecast Day", row=1, col=1)
        fig.update_xaxes(title_text="Forecast Day", row=2, col=1)
        fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
        fig.update_yaxes(title_text="Change (%)", row=2, col=1)
        
        fig.update_layout(
            height=700,
            template="plotly_white",
            font=dict(size=12),
            hovermode="x unified"
        )
        
        return fig
    
    except Exception as e:
        print(f"❌ Error creating price change plot: {e}")
        return None

# ============= Visualization: All Stocks Forecast Overview =============
def plot_all_stocks_forecast(forecast_files: list, symbols: list):
    """
    Create a grid of subplots showing forecast for all stocks
    """
    try:
        n_stocks = len(symbols)
        n_cols = 3
        n_rows = (n_stocks + n_cols - 1) // n_cols
        
        fig = make_subplots(
            rows=n_rows, cols=n_cols,
            subplot_titles=symbols,
            specs=[[{"secondary_y": False}] * n_cols for _ in range(n_rows)]
        )
        
        colors = {"linear": "blue", "moving_average": "orange", "arima": "green", "prophet": "red"}
        
        for idx, symbol in enumerate(symbols):
            row = (idx // n_cols) + 1
            col = (idx % n_cols) + 1
            
            for method, file_path in forecast_files:
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df = df[df["symbol"] == symbol].sort_values("timestamp")
                    
                    if not df.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=df["timestamp"],
                                y=df["predicted_close"],
                                name=method.upper(),
                                mode="lines+markers",
                                line=dict(color=colors.get(method, "black"), width=1),
                                marker=dict(size=4),
                                showlegend=(idx == 0),
                                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>₹%{y:.2f}<extra></extra>"
                            ),
                            row=row, col=col
                        )
            
            fig.update_xaxes(title_text="Date", row=row, col=col)
            fig.update_yaxes(title_text="Price (₹)", row=row, col=col)
        
        fig.update_layout(
            title_text="<b>7-Day Price Forecasts - All Stocks</b>",
            height=300 * n_rows,
            template="plotly_white",
            font=dict(size=10),
            hovermode="closest"
        )
        
        return fig
    
    except Exception as e:
        print(f"❌ Error creating overview plot: {e}")
        return None

# ============= Main Visualization Function =============
def generate_all_visualizations():
    """
    Generate all forecast visualizations
    """
    print("\n" + "=" * 70)
    print("📊 GENERATING FORECAST VISUALIZATIONS")
    print("=" * 70)
    
    TICKERS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "AAPL", "GOOG"]
    METHODS = ["linear", "moving_average", "arima", "prophet"]
    
    # Check which forecast files exist
    available_forecasts = []
    for method in METHODS:
        file_path = f"forecast_all_stocks_{method}.csv"
        if os.path.exists(file_path):
            available_forecasts.append((method, file_path))
    
    if not available_forecasts:
        print("⚠️ No forecast files found. Run stock_price_forecast.py first.")
        return
    
    print(f"Found forecasts for methods: {[m[0].upper() for m in available_forecasts]}\n")
    
    # 1. Generate multi-method comparison for each stock
    print("📈 Creating multi-method comparison charts...")
    for symbol in TICKERS:
        fig = plot_multi_method_comparison(symbol, available_forecasts)
        if fig:
            filename = f"forecast_{symbol.replace('.', '_')}_comparison.html"
            fig.write_html(filename)
            print(f"✔ Saved: {filename}")
    
    # 2. Generate detailed forecast+historical charts for each stock/method
    print("\n📉 Creating forecast vs historical charts...")
    for symbol in TICKERS:
        historical_df = fetch_historical_data(symbol, days=90)
        
        if not historical_df.empty:
            for method, forecast_file in available_forecasts:
                try:
                    forecast_df = pd.read_csv(forecast_file)
                    forecast_df = forecast_df[forecast_df["symbol"] == symbol]
                    forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"])
                    
                    if not forecast_df.empty:
                        fig = plot_forecast_vs_historical(historical_df, forecast_df, symbol, method.upper())
                        if fig:
                            filename = f"forecast_{symbol.replace('.', '_')}_{method}_detailed.html"
                            fig.write_html(filename)
                            print(f"✔ Saved: {filename}")
                except Exception as e:
                    print(f"⚠️ Skipping {symbol} {method}: {e}")
    
    # 3. Generate price change visualizations
    print("\n💹 Creating price change charts...")
    for symbol in TICKERS:
        for method, forecast_file in available_forecasts:
            try:
                forecast_df = pd.read_csv(forecast_file)
                forecast_df = forecast_df[forecast_df["symbol"] == symbol]
                
                if not forecast_df.empty:
                    fig = plot_price_change_comparison(forecast_df, symbol, method.upper())
                    if fig:
                        filename = f"forecast_{symbol.replace('.', '_')}_{method}_changes.html"
                        fig.write_html(filename)
                        print(f"✔ Saved: {filename}")
            except Exception as e:
                print(f"⚠️ Skipping {symbol} {method}: {e}")
    
    # 4. Generate overview grid
    print("\n🎯 Creating overview grid...")
    fig = plot_all_stocks_forecast(available_forecasts, TICKERS)
    if fig:
        fig.write_html("forecast_all_stocks_overview.html")
        print("✔ Saved: forecast_all_stocks_overview.html")
    
    print("\n" + "=" * 70)
    print("✨ Visualization generation completed!")
    print("=" * 70)
    
    print("\n📁 Generated HTML Files:")
    print("  • forecast_{symbol}_comparison.html")
    print("  • forecast_{symbol}_{method}_detailed.html")
    print("  • forecast_{symbol}_{method}_changes.html")
    print("  • forecast_all_stocks_overview.html")
    print("\nOpen any .html file in your browser to view interactive charts!")

# ============= Main Execution =============
if __name__ == "__main__":
    generate_all_visualizations()
