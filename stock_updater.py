from celery import Celery
from datetime import timedelta
import mysql.connector
import requests
from flask import jsonify

# Initialize Celery with Redis as the message broker
app = Celery('tasks', broker='redis://localhost:6379/0')

# Define your Polygon API key
API_KEY = "onNX6t8vQlxkS8WNPpr1ExYEGNCkiyvl"

# Define function to fetch current price and update database
@app.task
def update_stock_price(symbol):
    try:
        # Fetch current price of the stock
        stock_price = fetch_current_price(symbol)

        # Update the stock price in the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="abhi992744",
            database="tradeplay_credentials"
        )
        cursor = conn.cursor()
        cursor.execute('UPDATE portfolio SET price = %s WHERE stock = %s', (stock_price, symbol))
        cursor.execute('UPDATE portfolio SET total_value = price * quantity WHERE stock = %s', (symbol,))
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error updating stock price for {symbol}: {e}")

# Fetch stock price from API
def fetch_current_price(symbol):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/5/minute/2024-04-29/2024-04-29?adjusted=true&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            return data['results'][0]['c']  # Closing price
    return None
    pass

def get_stock_symbols():
    try:
        response = requests.get('https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit=1000&apiKey=onNX6t8vQlxkS8WNPpr1ExYEGNCkiyvl')
        if response.status_code == 200:
            data = response.json()
            symbols = [result['ticker'] for result in data['results']]
            return jsonify({'symbols': symbols})
        else:
            return jsonify({'error': 'Failed to fetch stock symbols from API'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    pass


# Get stock symbols
stock_symbols = get_stock_symbols()

# Define Celery beat schedule dynamically for each symbol
beat_schedule = {
    f'update-stocks-every-minute-{symbol}': {
        'task': 'update_stock_price',
        'schedule': timedelta(seconds=60),
        'args': (symbol,)
    }
    for symbol in stock_symbols
}

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use logging
logging.info("This is an information message")
logging.error("This is an error message")
