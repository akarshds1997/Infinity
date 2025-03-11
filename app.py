from flask import Flask
import threading
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import sys

app = Flask(__name__)

# Telegram Bot Details
TELEGRAM_TOKEN = "79"
CHAT_ID = "7"

# Binance API URL
BINANCE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "ETHUSDT"
INTERVAL = "5m"

def get_bbw():
    params = {"symbol": SYMBOL, "interval": INTERVAL, "limit": 50}
    response = requests.get(BINANCE_URL, params=params)
    data = response.json()
    
    if not isinstance(data, list):
        return None
    
    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"])
    df["close"] = df["close"].astype(float)
    
    if len(df) < 20:
        return None
    
    df["SMA"] = df["close"].rolling(window=20).mean()
    df["STD"] = df["close"].rolling(window=20).std()
    df["Upper"] = df["SMA"] + (df["STD"] * 2)
    df["Lower"] = df["SMA"] - (df["STD"] * 2)
    df["BBW"] = (df["Upper"] - df["Lower"]) / df["SMA"]
    
    return df["BBW"].dropna().round(4).values if len(df) >= 5 else None

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}
    requests.get(url, params=params)

def monitor_live_bbw():
    prev_live_bbw = None
    while True:
        bbw_values = get_bbw()
        if bbw_values is not None and len(bbw_values) >= 1:
            curr_live_bbw = bbw_values[-1]
            
            # Compare with previous live BBW value
            if prev_live_bbw is not None and (curr_live_bbw - prev_live_bbw) > 0.0010:
                send_telegram_alert(f"ETHUSDT Live BBW Increased: {curr_live_bbw}")
                time.sleep(60)  # Wait 60 seconds before sending another live alert
            
            prev_live_bbw = curr_live_bbw
            
            # Display live BBW in real-time
            sys.stdout.write(f"\r\033[91mLive BBW: {curr_live_bbw}\033[0m   ")
            sys.stdout.flush()
        
        time.sleep(5)

def monitor_candlestick_bbw():
    while True:
        bbw_values = get_bbw()
        if bbw_values is not None and len(bbw_values) >= 5:
            prev_bbw1, prev_bbw2, curr_bbw = bbw_values[-3], bbw_values[-2], bbw_values[-1]
            bbw_diff1 = round(curr_bbw - prev_bbw1, 4)
            bbw_diff2 = round(curr_bbw - prev_bbw2, 4)
            
            print(f"\nPrevious 5 BBW values: {bbw_values[-5:]}")
            print(f"Previous BBW1: {prev_bbw1}, Previous BBW2: {prev_bbw2}, Current BBW: {curr_bbw}")
            print(f"Differences: {bbw_diff1}, {bbw_diff2}")
            
            # Compare with either of the last two candlestick BBW values
            if (bbw_diff1 >= 0.0010 and curr_bbw > prev_bbw1) or (bbw_diff2 >= 0.0010 and curr_bbw > prev_bbw2):
                send_telegram_alert("5min ETH/USDT BBW +10")
        
        time.sleep(300)  # Check every 5 minutes

@app.route('/')
def home():
    return "BBW Monitoring Service is Running!"

# Start monitoring in background threads
threading.Thread(target=monitor_live_bbw, daemon=True).start()
threading.Thread(target=monitor_candlestick_bbw, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
