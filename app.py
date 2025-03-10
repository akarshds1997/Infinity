from flask import Flask, request, render_template
from flask_basicauth import BasicAuth

app = Flask(__name__)

# Secure with Basic Auth
app.config['BASIC_AUTH_USERNAME'] = 'Infinity'   # Change username
app.config['BASIC_AUTH_PASSWORD'] = 'MvEmJsUnP'  # Change password
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)

@app.route('/')
@basic_auth.required
def run_python():
    return "Python code is running when this page loads!"

import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import threading
import sys

# Telegram Bot Details
TELEGRAM_TOKEN = "7940671062:AAHEMb7l7SlgBKf0ffgkNU5QS3gfEoTJfc8"
CHAT_ID = "732675509"

# Binance API URL (No API Key Required)
BINANCE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "ETHUSDT"
INTERVAL = "5m"

def get_bbw():
    params = {"symbol": SYMBOL, "interval": INTERVAL, "limit": 50}
    response = requests.get(BINANCE_URL, params=params)
    data = response.json()
    
    if not isinstance(data, list):
        print("Error fetching data from Binance:", data)
        return None
    
    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"])
    df["close"] = df["close"].astype(float)
    
    if len(df) < 20:
        print("Not enough data for BBW calculation.")
        return None
    
    df["SMA"] = df["close"].rolling(window=20).mean()
    df["STD"] = df["close"].rolling(window=20).std()
    df["Upper"] = df["SMA"] + (df["STD"] * 2)
    df["Lower"] = df["SMA"] - (df["STD"] * 2)
    df["BBW"] = (df["Upper"] - df["Lower"]) / df["SMA"]
    
    bbw_values = df["BBW"].dropna().round(4).values
    return bbw_values if len(bbw_values) >= 5 else None

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}
    requests.get(url, params=params)

def monitor_live_bbw():
    prev_candle_bbw = None
    while prev_candle_bbw is None:
        bbw_values = get_bbw()
        if bbw_values is not None and len(bbw_values) >= 2:
            prev_candle_bbw = bbw_values[-2]  # Already formed previous candlestick BBW
            print(f"Previous Candlestick BBW: {prev_candle_bbw}")
        time.sleep(5)
    
    while True:
        bbw_values = get_bbw()
        if bbw_values is not None and len(bbw_values) >= 1:
            curr_bbw = bbw_values[-1]
            if curr_bbw > prev_candle_bbw:
                send_telegram_alert("ETHUSDT Live BBW +10")
                print(f"Live BBW Alert Sent! Exceeded Previous BBW: {prev_candle_bbw}")
                prev_candle_bbw = curr_bbw  # Update reference BBW
        
        sys.stdout.write(f"\r\033[91mLive BBW: {curr_bbw}\033[0m   ")  # Red color output
        sys.stdout.flush()
        time.sleep(5)

threading.Thread(target=monitor_live_bbw, daemon=True).start()

print("Starting BBW Monitoring...")
while True:
    try:
        now = datetime.now(timezone.utc)
        next_minute = (now.minute // 5 + 1) * 5
        if next_minute >= 60:
            next_candle_time = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
        else:
            next_candle_time = now.replace(minute=next_minute, second=0, microsecond=0)
        wait_time = (next_candle_time - now).total_seconds()
        
        while wait_time > 0:
            sys.stdout.write(f"\rCountdown: {int(wait_time)}s until next 5m candlestick...   ")
            sys.stdout.flush()
            time.sleep(1)
            wait_time -= 1
        
        print("\nFetching new candlestick data...")
        bbw_values = get_bbw()
        if bbw_values is not None and len(bbw_values) >= 5:
            prev_bbw1, prev_bbw2, curr_bbw = bbw_values[-3], bbw_values[-2], bbw_values[-1]
            bbw_diff1 = round(curr_bbw - prev_bbw1, 4)
            bbw_diff2 = round(curr_bbw - prev_bbw2, 4)
            
            print(f"Previous 5 BBW values: {bbw_values[-5:]}")
            print(f"Previous BBW1: {prev_bbw1}, Previous BBW2: {prev_bbw2}, Current BBW: {curr_bbw}")
            print(f"Differences: {bbw_diff1}, {bbw_diff2}")
            
            if (bbw_diff1 >= 0.0010 and curr_bbw > prev_bbw1) or (bbw_diff2 >= 0.0010 and curr_bbw > prev_bbw2):
                send_telegram_alert("5min ETH/USDT BBW +10")
                print(f"BBW Alert Sent! Increase detected.")
            else:
                print(f"BBW Change: {bbw_diff1}, {bbw_diff2} (No Alert, Not a +0.0010 Increase)")
        else:
            print("Waiting for sufficient data...")
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(1)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
