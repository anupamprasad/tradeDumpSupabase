import ccxt
import pandas as pd

exchange = ccxt.binance()
symbol = 'BTC/USDT'

data = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=5000)

df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df.to_csv("btc_data.csv", index=False)
