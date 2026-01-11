import yfinance as yf
import time

# print("Waiting 10 seconds before request...")
# time.sleep(10)

# print("Fetching with session...")
# import requests
# session = requests.Session()
# session.headers['User-Agent'] = 'Mozilla/5.0'

# ticker = yf.Ticker("RELIANCE.NS", session=session)
# data = ticker.history(period="5d")  # Just 5 days to be safe

# print(f"Success! Got {len(data)} rows")
# print(data)

import yfinance as yf

data = yf.download(
    "RELIANCE.NS",
    period="5d",
    interval="1d",
    progress=False,
    threads=False   # VERY IMPORTANT
)

print(data)
