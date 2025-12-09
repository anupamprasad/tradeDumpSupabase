import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Stock Forecast Dashboard", layout="wide", initial_sidebar_state="expanded")

st.title("📈 Stock Price Forecast Dashboard")
st.markdown("Interactive visualization of 7-day stock price forecasts using multiple methods")

# ============= Supabase Configuration =============
@st.cache_resource
def get_supabase_client():
    """Get Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_API_KEY")
    
    if not url or not key:
        st.error("❌ Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_API_KEY environment variables.")
        st.stop()
    
    return create_client(url, key)

# ============= Load Forecast Data from Supabase =============
@st.cache_data(ttl=300)
def load_forecast_data_from_supabase():
    """Load forecast data from Supabase table"""
    try:
        supabase = get_supabase_client()
        
        # Fetch all forecasts from Supabase
        response = supabase.table("forecast_stocks").select("*").execute()
        
        if not response.data or len(response.data) == 0:
            st.error("❌ No forecast data found in Supabase. Please run store_forecasts_to_supabase_v2.py first.")
            st.stop()
        
        # Convert to DataFrame
        df = pd.DataFrame(response.data)
        df["forecast_date"] = pd.to_datetime(df["forecast_date"])
        
        # Group by method for easier access
        forecasts = {}
        for method in df["method"].unique():
            forecasts[method] = df[df["method"] == method].copy()
            st.success(f"✔ Loaded {method} forecasts ({len(forecasts[method])} records)")
        
        return forecasts
    
    except Exception as e:
        st.error(f"❌ Error loading data from Supabase: {e}")
        st.info("📝 Make sure your .env file has SUPABASE_URL and SUPABASE_API_KEY")
        st.stop()

# Load data
forecasts = load_forecast_data_from_supabase()

if not forecasts:
    st.error("❌ No forecast data found. Please run stock_price_forecast.py and store_forecasts_to_supabase_v2.py first.")
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
        symbol_data = df[df["symbol"] == selected_symbol].sort_values("forecast_date")
        
        if not symbol_data.empty:
            fig.add_trace(go.Scatter(
                x=symbol_data["forecast_date"],
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
                "Avg Change %": f"{symbol_data['price_change_pct'].mean():.2f}%" if 'price_change_pct' in symbol_data.columns else "N/A"
            })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ============= Tab 2: Detailed Forecast =============
with tab2:
    st.subheader(f"Detailed Forecast - {selected_symbol}")
    
    if selected_methods:
        method_choice = st.radio("Select Method", selected_methods, horizontal=True)
        
        df = forecasts[method_choice]
        symbol_data = df[df["symbol"] == selected_symbol].sort_values("forecast_date")
        
        if not symbol_data.empty:
            fig = go.Figure()
            
            # Main forecast line
            fig.add_trace(go.Scatter(
                x=symbol_data["forecast_date"],
                y=symbol_data["predicted_close"],
                name="Predicted Price",
                mode="lines+markers",
                line=dict(color="#2ca02c", width=3),
                marker=dict(size=10),
                hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>"
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
    
    if selected_methods:
        method_choice_3 = st.radio("Select Method", selected_methods, horizontal=True, key="method3")
        
        df = forecasts[method_choice_3]
        symbol_data = df[df["symbol"] == selected_symbol].sort_values("forecast_date")
        
        if not symbol_data.empty:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(
                    f"{selected_symbol} - Predicted Price",
                    f"{selected_symbol} - Price Change %"
                ),
                specs=[[{}], [{}]]
            )
            
            # Price trend
            fig.add_trace(
                go.Scatter(
                    x=symbol_data["forecast_date"],
                    y=symbol_data["predicted_close"],
                    name="Predicted Price",
                    mode="lines+markers",
                    line=dict(color="#1f77b4", width=2),
                    marker=dict(size=10),
                    hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> ₹%{y:.2f}<extra></extra>"
                ),
                row=1, col=1
            )
            
            # Price change bars
            if 'price_change_pct' in symbol_data.columns:
                colors = ["green" if x >= 0 else "red" for x in symbol_data["price_change_pct"]]
                fig.add_trace(
                    go.Bar(
                        x=symbol_data["forecast_date"],
                        y=symbol_data["price_change_pct"],
                        name="% Change",
                        marker=dict(color=colors),
                        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Change:</b> %{y:.2f}%<extra></extra>"
                    ),
                    row=2, col=1
                )
            
            # Update layout
            fig.update_xaxes(title_text="Date", row=1, col=1)
            fig.update_xaxes(title_text="Date", row=2, col=1)
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
    
    if selected_methods:
        method_choice_4 = st.radio("Select Method", selected_methods, horizontal=True, key="method4")
        
        df = forecasts[method_choice_4]
        symbol_data = df[df["symbol"] == selected_symbol].sort_values("forecast_date")
        
        if not symbol_data.empty:
            # Display columns
            display_cols = ["forecast_date", "predicted_close", "price_change", "price_change_pct"]
            display_cols = [col for col in display_cols if col in symbol_data.columns]
            
            # Format the dataframe for display
            display_df = symbol_data[display_cols].copy()
            display_df["forecast_date"] = display_df["forecast_date"].dt.strftime("%Y-%m-%d")
            
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
st.markdown("📊 Data from: Supabase (forecast_stocks table)")
st.markdown("🔄 Refresh data: Press R or wait 5 minutes for auto-refresh")
