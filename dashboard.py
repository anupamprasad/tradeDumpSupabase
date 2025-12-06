import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

import numpy as np

load_dotenv()

# ============= Config =============
st.set_page_config(page_title="Stock Prices Dashboard", layout="wide", initial_sidebar_state="expanded")

# ============= Supabase Init =============
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Missing SUPABASE_URL or SUPABASE_API_KEY environment variables")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============= Cached Data Fetch =============
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_stock_data():
    try:
        response = supabase.table("stock_prices").select("*").execute()
        data = response.data
        if not data:
            st.warning("⚠️ No data in stock_prices table")
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # Convert timestamp to datetime if it exists
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

# ============= App Title & Header =============
st.title("📈 Stock Prices Dashboard")
st.markdown("Real-time stock price monitoring from Supabase")

# ============= Fetch Data =============
df = fetch_stock_data()

if df.empty:
    st.info("No data available. Please ensure the stock_prices table is populated.")
    st.stop()

# ============= Sidebar Filters =============
st.sidebar.header("🔍 Filters")

# Get unique symbols
symbols = sorted(df["symbol"].unique()) if "symbol" in df.columns else []
selected_symbols = st.sidebar.multiselect("Select Symbols", symbols, default=symbols[:3] if len(symbols) > 0 else [])

# Date range filter
if "timestamp" in df.columns:
    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()
    # Ensure default start date doesn't go before min_date
    default_start = max(max_date - timedelta(days=30), min_date)
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(default_start, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

# ============= Filter Data =============
filtered_df = df.copy()

if selected_symbols:
    filtered_df = filtered_df[filtered_df["symbol"].isin(selected_symbols)]

if date_range and "timestamp" in df.columns:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["timestamp"].dt.date >= start_date) &
        (filtered_df["timestamp"].dt.date <= end_date)
    ]

# ============= Key Metrics =============
st.subheader("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

if "close" in filtered_df.columns:
    avg_close = filtered_df["close"].mean()
    col1.metric("Avg Close Price", f"₹ {avg_close:.2f}" if avg_close < 1000 else f"$ {avg_close:.2f}")

if "volume" in filtered_df.columns:
    total_volume = filtered_df["volume"].sum()
    col2.metric("Total Volume", f"{total_volume:.0f}")

if "high" in filtered_df.columns:
    max_high = filtered_df["high"].max()
    col3.metric("Max High", f"₹ {max_high:.2f}" if max_high < 1000 else f"$ {max_high:.2f}")

if "low" in filtered_df.columns:
    min_low = filtered_df["low"].min()
    col4.metric("Min Low", f"₹ {min_low:.2f}" if min_low < 1000 else f"$ {min_low:.2f}")

# ============= Charts =============
st.subheader("📉 Price Trends & Analysis")

# Chart 1: Close Price with Moving Averages
if "timestamp" in filtered_df.columns and "close" in filtered_df.columns:
    st.markdown("#### Close Price with Moving Averages (7-day & 30-day)")
    
    df_ma = filtered_df.copy()
    df_ma = df_ma.sort_values("timestamp")
    
    # Calculate moving averages per symbol
    for symbol in df_ma["symbol"].unique():
        mask = df_ma["symbol"] == symbol
        df_ma.loc[mask, "MA7"] = df_ma.loc[mask, "close"].rolling(window=7, min_periods=1).mean()
        df_ma.loc[mask, "MA30"] = df_ma.loc[mask, "close"].rolling(window=30, min_periods=1).mean()
    
    fig_ma = go.Figure()
    
    for symbol in df_ma["symbol"].unique():
        symbol_data = df_ma[df_ma["symbol"] == symbol]
        
        fig_ma.add_trace(go.Scatter(
            x=symbol_data["timestamp"],
            y=symbol_data["close"],
            name=f"{symbol} Close",
            mode="lines",
            line=dict(width=2)
        ))
        
        fig_ma.add_trace(go.Scatter(
            x=symbol_data["timestamp"],
            y=symbol_data["MA7"],
            name=f"{symbol} MA7",
            mode="lines",
            line=dict(width=1, dash="dash"),
            opacity=0.7
        ))
        
        fig_ma.add_trace(go.Scatter(
            x=symbol_data["timestamp"],
            y=symbol_data["MA30"],
            name=f"{symbol} MA30",
            mode="lines",
            line=dict(width=1, dash="dot"),
            opacity=0.7
        ))
    
    fig_ma.update_layout(height=450, hovermode="x unified")
    st.plotly_chart(fig_ma, use_container_width=True)

# Chart 2: Volatility (20-day Rolling Std Dev)
if "timestamp" in filtered_df.columns and "close" in filtered_df.columns:
    st.markdown("#### 20-Day Rolling Volatility (Std Dev)")
    
    df_vol = filtered_df.copy()
    df_vol = df_vol.sort_values("timestamp")
    
    for symbol in df_vol["symbol"].unique():
        mask = df_vol["symbol"] == symbol
        df_vol.loc[mask, "volatility"] = df_vol.loc[mask, "close"].rolling(window=20, min_periods=1).std()
    
    fig_vol = px.line(
        df_vol,
        x="timestamp",
        y="volatility",
        color="symbol",
        title="20-Day Rolling Volatility",
        labels={"volatility": "Volatility (Std Dev)", "timestamp": "Date", "symbol": "Symbol"}
    )
    fig_vol.update_layout(height=350, hovermode="x unified")
    st.plotly_chart(fig_vol, use_container_width=True)

# Chart 3: Normalized Price Comparison (% change from first date)
if "timestamp" in filtered_df.columns and "close" in filtered_df.columns and len(selected_symbols) > 1:
    st.markdown("#### Normalized Price Comparison (% Change from Start)")
    
    df_norm = filtered_df.copy()
    df_norm = df_norm.sort_values("timestamp")
    
    for symbol in df_norm["symbol"].unique():
        mask = df_norm["symbol"] == symbol
        first_price = df_norm.loc[mask, "close"].iloc[0] if len(df_norm.loc[mask]) > 0 else 1
        df_norm.loc[mask, "normalized"] = ((df_norm.loc[mask, "close"] - first_price) / first_price) * 100
    
    fig_norm = px.line(
        df_norm,
        x="timestamp",
        y="normalized",
        color="symbol",
        title="Normalized Price Comparison",
        labels={"normalized": "% Change from Start", "timestamp": "Date", "symbol": "Symbol"}
    )
    fig_norm.update_layout(height=400, hovermode="x unified")
    st.plotly_chart(fig_norm, use_container_width=True)

# Chart 4: OHLC Candlestick (single symbol only)
if len(selected_symbols) == 1 and "timestamp" in filtered_df.columns:
    symbol = selected_symbols[0]
    symbol_data = filtered_df[filtered_df["symbol"] == symbol].sort_values("timestamp")
    
    if not symbol_data.empty and all(col in symbol_data.columns for col in ["open", "high", "low", "close"]):
        st.markdown(f"#### OHLC Candlestick - {symbol}")
        fig_candle = go.Figure(data=[go.Candlestick(
            x=symbol_data["timestamp"],
            open=symbol_data["open"],
            high=symbol_data["high"],
            low=symbol_data["low"],
            close=symbol_data["close"]
        )])
        fig_candle.update_layout(height=450)
        st.plotly_chart(fig_candle, use_container_width=True)

# Chart 5: Volume
if "timestamp" in filtered_df.columns and "volume" in filtered_df.columns:
    st.markdown("#### Trading Volume")
    fig_volume = px.bar(
        filtered_df,
        x="timestamp",
        y="volume",
        color="symbol",
        title="Daily Trading Volume",
        labels={"volume": "Volume", "timestamp": "Date", "symbol": "Symbol"}
    )
    fig_volume.update_layout(height=350, hovermode="x unified")
    st.plotly_chart(fig_volume, use_container_width=True)

# Chart 6: Price Range (High-Low Spread)
if "timestamp" in filtered_df.columns and "high" in filtered_df.columns and "low" in filtered_df.columns:
    st.markdown("#### Daily Price Range (High-Low Spread)")
    
    df_range = filtered_df.copy()
    df_range["range"] = df_range["high"] - df_range["low"]
    
    fig_range = px.bar(
        df_range,
        x="timestamp",
        y="range",
        color="symbol",
        title="Daily Price Range",
        labels={"range": "High - Low", "timestamp": "Date", "symbol": "Symbol"}
    )
    fig_range.update_layout(height=350, hovermode="x unified")
    st.plotly_chart(fig_range, use_container_width=True)

# ============= Data Table =============
st.subheader("📋 Data Table")
display_cols = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
display_cols = [col for col in display_cols if col in filtered_df.columns]

if display_cols:
    st.dataframe(
        filtered_df[display_cols].sort_values("timestamp", ascending=False),
        use_container_width=True,
        height=400
    )

# ============= Statistics =============
st.subheader("📈 Statistics Summary")

if "close" in filtered_df.columns and "symbol" in filtered_df.columns:
    stats_data = []
    for symbol in filtered_df["symbol"].unique():
        symbol_data = filtered_df[filtered_df["symbol"] == symbol]["close"]
        stats_data.append({
            "Symbol": symbol,
            "Min": f"₹ {symbol_data.min():.2f}" if symbol_data.min() < 1000 else f"$ {symbol_data.min():.2f}",
            "Max": f"₹ {symbol_data.max():.2f}" if symbol_data.max() < 1000 else f"$ {symbol_data.max():.2f}",
            "Mean": f"₹ {symbol_data.mean():.2f}" if symbol_data.mean() < 1000 else f"$ {symbol_data.mean():.2f}",
            "Std Dev": f"{symbol_data.std():.2f}",
            "Count": len(symbol_data)
        })
    
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

# ============= Footer =============
st.markdown("---")
st.markdown("✨ Dashboard powered by Streamlit & Supabase | Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
st.markdown("📊 Data from table: `stock_prices` | 🔄 Auto-refresh: 5 minutes")
