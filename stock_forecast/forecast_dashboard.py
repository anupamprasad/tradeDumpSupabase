import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime

st.set_page_config(page_title="Stock Forecast Dashboard", layout="wide", initial_sidebar_state="expanded")

st.title("📈 Stock Price Forecast Dashboard")
st.markdown("Interactive visualization of 7-day stock price forecasts using multiple methods")

# ============= Load Forecast Data =============
@st.cache_data(ttl=300)
def load_forecast_data():
    """Load all available forecast data"""
    forecasts = {}
    
    methods = ["linear", "moving_average", "arima", "prophet"]
    
    for method in methods:
        file_path = f"forecast_all_stocks_{method}.csv"
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                forecasts[method] = df
                st.success(f"✔ Loaded {method} forecasts")
            except Exception as e:
                st.warning(f"⚠️ Could not load {method} forecasts: {e}")
    
    return forecasts

# Load data
forecasts = load_forecast_data()

if not forecasts:
    st.error("❌ No forecast data found. Please run stock_price_forecast.py first.")
    st.stop()

# ============= Sidebar Filters =============
st.sidebar.header("🔍 Filters & Settings")

# Get unique symbols
symbols = sorted(list(set().union(*[df["symbol"].unique() for df in forecasts.values()])))
selected_symbol = st.sidebar.selectbox("Select Stock Symbol", symbols)

# Get available methods
available_methods = list(forecasts.keys())
selected_methods = st.sidebar.multiselect(
    "Select Forecasting Methods",
    available_methods,
    default=available_methods
)

# ============= Tab 1: Multi-Method Comparison =============
tab1, tab2, tab3, tab4 = st.tabs(["📊 Comparison", "📉 Details", "💹 Changes", "📋 Data"])

with tab1:
    st.subheader(f"Multi-Method Forecast Comparison - {selected_symbol}")
    
    fig = go.Figure()
    
    colors = {
        "linear": "#1f77b4",
        "moving_average": "#ff7f0e",
        "arima": "#2ca02c",
        "prophet": "#d62728"
    }
    
    for method in selected_methods:
        df = forecasts[method]
        symbol_data = df[df["symbol"] == selected_symbol].sort_values("timestamp")
        
        if not symbol_data.empty:
            fig.add_trace(go.Scatter(
                x=symbol_data["timestamp"],
                y=symbol_data["predicted_close"],
                name=method.upper(),
                mode="lines+markers",
                line=dict(color=colors.get(method, "#000000"), width=2),
                marker=dict(size=8),
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>"
            ))
    
    fig.update_layout(
        height=500,
        hovermode="x unified",
        template="plotly_white",
        xaxis_title="Date",
        yaxis_title="Predicted Price (₹)"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    st.markdown("#### 📊 Summary Statistics")
    
    summary_data = []
    for method in selected_methods:
        df = forecasts[method]
        symbol_data = df[df["symbol"] == selected_symbol]
        
        if not symbol_data.empty:
            summary_data.append({
                "Method": method.upper(),
                "Avg Price": f"₹{symbol_data['predicted_close'].mean():.2f}",
                "Min Price": f"₹{symbol_data['predicted_close'].min():.2f}",
                "Max Price": f"₹{symbol_data['predicted_close'].max():.2f}",
                "Avg Change %": f"{symbol_data['price_change_pct'].mean():.2f}%"
            })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ============= Tab 2: Detailed Forecast =============
with tab2:
    st.subheader(f"Detailed Forecast - {selected_symbol}")
    
    method_choice = st.radio("Select Method", selected_methods, horizontal=True)
    
    df = forecasts[method_choice]
    symbol_data = df[df["symbol"] == selected_symbol].sort_values("timestamp")
    
    if not symbol_data.empty:
        fig = go.Figure()
        
        # Main forecast line
        fig.add_trace(go.Scatter(
            x=symbol_data["timestamp"],
            y=symbol_data["predicted_close"],
            name="Predicted Price",
            mode="lines+markers",
            line=dict(color="#2ca02c", width=3),
            marker=dict(size=10),
            hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>"
        ))
        
        # Add confidence intervals if available
        if "upper_bound" in symbol_data.columns and "lower_bound" in symbol_data.columns:
            fig.add_trace(go.Scatter(
                x=symbol_data["timestamp"],
                y=symbol_data["upper_bound"],
                fill=None,
                mode="lines",
                line_color="rgba(0,0,0,0)",
                showlegend=False,
                hoverinfo="skip"
            ))
            
            fig.add_trace(go.Scatter(
                x=symbol_data["timestamp"],
                y=symbol_data["lower_bound"],
                fill="tonexty",
                mode="lines",
                line_color="rgba(0,0,0,0)",
                name="95% Confidence Interval",
                fillcolor="rgba(44, 160, 44, 0.2)",
                hoverinfo="skip"
            ))
        
        fig.update_layout(
            height=500,
            hovermode="x unified",
            template="plotly_white",
            xaxis_title="Date",
            yaxis_title="Predicted Price (₹)",
            title=f"{selected_symbol} - {method_choice.upper()} Forecast"
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============= Tab 3: Price Changes =============
with tab3:
    st.subheader(f"Predicted Price Changes - {selected_symbol}")
    
    method_choice_3 = st.radio("Select Method", selected_methods, horizontal=True, key="method3")
    
    df = forecasts[method_choice_3]
    symbol_data = df[df["symbol"] == selected_symbol].sort_values("forecast_day")
    
    if not symbol_data.empty:
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f"{selected_symbol} - Predicted Price by Day",
                f"{selected_symbol} - Price Change %"
            ),
            specs=[[{}], [{}]]
        )
        
        # Price trend
        fig.add_trace(
            go.Scatter(
                x=symbol_data["forecast_day"],
                y=symbol_data["predicted_close"],
                name="Predicted Price",
                mode="lines+markers",
                line=dict(color="#1f77b4", width=2),
                marker=dict(size=10),
                hovertemplate="<b>Day:</b> %{x}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Price change bars
        colors = ["green" if x >= 0 else "red" for x in symbol_data["price_change_pct"]]
        fig.add_trace(
            go.Bar(
                x=symbol_data["forecast_day"],
                y=symbol_data["price_change_pct"],
                name="% Change",
                marker=dict(color=colors),
                hovertemplate="<b>Day:</b> %{x}<br><b>Change:</b> %{y:.2f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_xaxes(title_text="Forecast Day", row=1, col=1)
        fig.update_xaxes(title_text="Forecast Day", row=2, col=1)
        fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
        fig.update_yaxes(title_text="Change (%)", row=2, col=1)
        
        fig.update_layout(
            height=700,
            template="plotly_white",
            hovermode="x unified",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ============= Tab 4: Data Table =============
with tab4:
    st.subheader(f"Forecast Data Table - {selected_symbol}")
    
    method_choice_4 = st.radio("Select Method", selected_methods, horizontal=True, key="method4")
    
    df = forecasts[method_choice_4]
    symbol_data = df[df["symbol"] == selected_symbol].sort_values("timestamp")
    
    if not symbol_data.empty:
        # Display columns
        display_cols = ["timestamp", "predicted_close", "price_change", "price_change_pct"]
        
        # Add confidence intervals if available
        if "upper_bound" in symbol_data.columns:
            display_cols.extend(["lower_bound", "upper_bound"])
        
        display_cols = [col for col in display_cols if col in symbol_data.columns]
        
        # Format the dataframe for display
        display_df = symbol_data[display_cols].copy()
        display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d")
        
        # Format numeric columns
        for col in display_df.columns:
            if col != "timestamp":
                display_df[col] = display_df[col].apply(lambda x: f"₹{x:.2f}" if col == "predicted_close" else f"{x:.2f}" if isinstance(x, float) else x)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = symbol_data[display_cols].to_csv(index=False)
        st.download_button(
            label=f"Download {selected_symbol} {method_choice_4.upper()} Forecast",
            data=csv,
            file_name=f"forecast_{selected_symbol.replace('.', '_')}_{method_choice_4}.csv",
            mime="text/csv"
        )

# ============= Footer =============
st.markdown("---")
st.markdown(f"✨ Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("📊 Generate forecasts with: `python3 stock_price_forecast.py`")
