# Stock Prices Dashboard

A real-time interactive dashboard to visualize stock price data stored in Supabase.

## Features

- 📈 **Live Stock Charts**: View close price trends, OHLC candlesticks, and trading volume
- 🔍 **Filters**: Filter by symbol and date range
- 📊 **Key Metrics**: Display average close, total volume, max high, and min low
- 📋 **Data Table**: Browse raw stock price data
- ⚡ **Fast**: 5-minute caching to reduce API calls

## Setup

### Prerequisites

- Python 3.8+
- Supabase account with a `stock_prices` table

### Installation

1. Install dependencies:
```bash
pip install -r dashboard_requirements.txt
```

2. Create a `.env` file in the project directory with:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=your-anon-key
```

### Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open at `http://localhost:8501`

## Table Schema

The dashboard expects a `stock_prices` table with columns:
- `timestamp` (datetime): When the price was recorded
- `symbol` (string): Stock ticker (e.g., AAPL, RELIANCE.NS)
- `open` (float): Opening price
- `high` (float): Highest price
- `low` (float): Lowest price
- `close` (float): Closing price
- `volume` (float): Trading volume

## Deployment

### Streamlit Cloud

1. Push your repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and deploy
4. Add secrets in Streamlit Cloud settings:
   - `SUPABASE_URL`
   - `SUPABASE_API_KEY`

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r dashboard_requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "dashboard.py"]
```

## Notes

- Data is cached for 5 minutes to reduce API load
- The dashboard automatically detects currency (₹ for < 1000, $ otherwise)
- OHLC candlestick chart only shows when a single symbol is selected
