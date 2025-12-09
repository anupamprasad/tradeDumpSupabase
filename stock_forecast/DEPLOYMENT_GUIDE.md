# 🚀 Deploy Forecast Dashboard to Streamlit Cloud

## Prerequisites

1. **GitHub Account** - Required for Streamlit Cloud deployment
2. **Supabase Credentials** - SUPABASE_URL and SUPABASE_API_KEY
3. **Streamlit Cloud Account** - Free tier available at https://streamlit.io/cloud

## Deployment Steps

### Step 1: Prepare Your Repository

Make sure your GitHub repository has:
- `stock_forecast/forecast_dashboard_supabase.py` - Main dashboard file
- `stock_forecast/requirements_deploy.txt` - Python dependencies
- `stock_forecast/.streamlit/config.toml` - Streamlit configuration
- `.env` file (locally only, not pushed to GitHub)

**Push to GitHub:**
```bash
cd /Users/anupamprasad/Documents/Python_File
git add stock_forecast/forecast_dashboard_supabase.py
git add stock_forecast/requirements_deploy.txt
git add stock_forecast/.streamlit/config.toml
git commit -m "Add Supabase-integrated forecast dashboard for deployment"
git push origin main
```

### Step 2: Create Streamlit Cloud App

1. Go to **https://share.streamlit.io/**
2. Click **"New app"**
3. Select your GitHub repository: `anupamprasad/tradeDumpSupabase`
4. Set branch to: `main`
5. Set main file path to: `stock_forecast/forecast_dashboard_supabase.py`
6. Click **"Deploy"**

### Step 3: Configure Secrets in Streamlit Cloud

After deployment (even if it fails initially), go to your app's settings:

1. Click the **⋮** (three dots) in the top-right → **Settings**
2. Go to **Secrets** section
3. Add your environment variables:

```
SUPABASE_URL = "your_supabase_url_here"
SUPABASE_API_KEY = "your_supabase_api_key_here"
```

4. Click **Save**
5. Streamlit will automatically redeploy with the new secrets

### Step 4: Verify Deployment

- Your dashboard will be live at: `https://share.streamlit.io/<your-username>/<app-name>`
- It will automatically pull data from your Supabase `forecast_stocks` table
- Data refreshes every 5 minutes

## Automated Deployment Updates

Every time you:
1. Run forecast generation: `python3 stock_price_forecast.py`
2. Store to Supabase: `python3 store_forecasts_to_supabase_v2.py store`

The dashboard will automatically show the latest data (within 5 minutes) without redeployment.

## Troubleshooting

### App shows "No forecast data found"
- Check that Supabase credentials are correctly set in Secrets
- Verify the `forecast_stocks` table has data: `python3 store_forecasts_to_supabase_v2.py display`

### "Missing Supabase credentials" error
- Go back to Streamlit Cloud app settings → Secrets
- Ensure SUPABASE_URL and SUPABASE_API_KEY are set correctly
- No leading/trailing spaces

### App times out on first load
- This is normal for the first load from Streamlit Cloud
- Data will cache after first successful load
- Subsequent loads are much faster

## Local Testing Before Deployment

Test the dashboard locally before deploying:

```bash
cd /Users/anupamparsad/Documents/Python_File/stock_forecast
/Users/anupamprasad/Documents/Python_File/.venv_new/bin/python -m streamlit run forecast_dashboard_supabase.py
```

Open: **http://localhost:8501**

## Public URL Once Deployed

After successful deployment, your dashboard will be available at:
```
https://share.streamlit.io/<your-username>/<app-name>
```

You can share this link with others to view your stock forecast dashboard!

## Features

✅ Multi-method forecast comparison (Linear, Moving Average, ARIMA, Prophet)
✅ Interactive Plotly charts with hover details
✅ Filter by stock symbol and forecasting method
✅ Summary statistics and price change analysis
✅ Download forecast data as CSV
✅ Real-time data from Supabase
✅ Auto-refreshing every 5 minutes

---

**Note:** Keep your Supabase API key secret! Never commit `.env` file to GitHub. Use Streamlit Cloud's Secrets management for credentials.
