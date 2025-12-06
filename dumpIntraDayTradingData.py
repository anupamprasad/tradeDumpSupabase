import yfinance as yf

data = yf.download("RELIANCE.NS", period="5d", interval="5m")
data.to_csv("reliance_5min.csv")