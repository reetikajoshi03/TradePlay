from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask import jsonify
import requests
import datetime
# Replace 'ARDO3QVA3649P4AK' with your actual Alpha Vantage API key (for this session only)
API_KEY = 'onNX6t8vQlxkS8WNPpr1ExYEGNCkiyvl'


def fetch_stock_data(symbol):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/5/minute/2024-04-29/2024-04-29?adjusted=true&sort=desc&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            results = data['results']
            # Iterate over each result and convert timestamp to date and time
            for result in results:
                timestamp = result['t'] / 1000  # Convert milliseconds to seconds
                result['datetime'] = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            return results
    return None

from datetime import datetime, timedelta

def fetch_current_price(symbol):
    # Get current timestamp and timestamp 2 days back
    current_timestamp = int(datetime.now().timestamp()) * 1000
    print(current_timestamp)
    two_days_ago_timestamp = int((datetime.now() - timedelta(days=2)).timestamp()) * 1000
    print(two_days_ago_timestamp)
    # API request URL with date range
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/5/minute/{two_days_ago_timestamp}/{current_timestamp}?adjusted=true&apiKey={API_KEY}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            for result in data['results']:
                if result['t'] == two_days_ago_timestamp:
                    return result['c']  # Closing price at two days ago timestamp
    return None

      
# Example usage (fetching 1-minute intraday data for AAPL)
symbol = "AAPL"
data = fetch_current_price(symbol)
if data:
  # Access data using the dictionary structure returned by the API
  print(data)
else:
  print("Failed to fetch data")
