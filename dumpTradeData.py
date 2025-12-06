import yfinance as yf

# Choose your symbol

ticker = yf.Ticker("AAPL")   # For NSE use "RELIANCE.NS"

# Download daily data

data = ticker.history(period="1y", interval="1d")

# Save to CSV

data.to_csv("aapl_data.csv")

print("Data dumped successfully!")
