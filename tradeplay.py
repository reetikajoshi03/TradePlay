# Import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask import jsonify
import requests
import datetime
# from stocks import get_stock_data

app = Flask(__name__)
app.secret_key = 'your_secret_key' 
 
# Define your Polygon API key
API_KEY = "onNX6t8vQlxkS8WNPpr1ExYEGNCkiyvl"

# MySQL database setup
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="abhi992744",
    database="tradeplay_credentials"
)
cursor = conn.cursor()

# Create users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        balance DECIMAL(10,3) NOT NULL DEFAULT 10000.000
    )
''')

# Create portfolio table
cursor.execute('''
CREATE TABLE IF NOT EXISTS portfolio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    stock VARCHAR(255),
    quantity INT,
    price DECIMAL(10,2),
    total_value DECIMAL(10,2),
    action VARCHAR(10)
    )
''')

# Create transaction table
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    stock VARCHAR(255),
    quantity INT,
    price DECIMAL(10,2),
    total_value DECIMAL(10,2),
    action VARCHAR(10),
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()


# Route for the dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        # Retrieve user details from the session
        username = session['username']
        
        # Fetch the user's balance from the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="abhi992744",
            database="tradeplay_credentials"
        )
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE username = %s', (username,))
        balance = cursor.fetchone()[0]
        conn.close()
        
        return render_template('dashboard.html', username=username, balance=balance)
    else:
        # Redirect the user to the login page if not authenticated
        return redirect(url_for('login'))



# Route for the home page (index page)
@app.route('/')
def index():
    if 'username' in session:
        # Retrieve user details from the session
        username = session['username']
        
        # Fetch recent transactions from the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="abhi992744",
            database="tradeplay_credentials"
        )
        cursor = conn.cursor()
        
        # Fetch recent transactions
        cursor.execute('SELECT * FROM transactions WHERE username = %s ORDER BY transaction_time DESC', (username,))
        recent_transactions = cursor.fetchall()
        
        # Define the stock symbols you want to display
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]  # Add more symbols as needed
        
        # Fetch current prices for the stock symbols
        current_prices = {}
        for symbol in symbols:
            price = fetch_current_price(symbol)
            current_prices[symbol] = price
        
        conn.close()
        
        return render_template('index.html', username=username, recent_transactions=recent_transactions, symbol=symbol, current_prices=current_prices)
    else:
        # Render the home page template directly
        return render_template('index.html')



def fetch_stock_data(symbol):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/5/minute/2024-04-30/2024-04-30?adjusted=true&sort=desc&apiKey={API_KEY}"
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

# Function to fetch stock price
def fetch_current_price(symbol):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/5/minute/2024-04-30/2024-04-30?adjusted=true&sort=desc&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            return data['results'][0]['c']  # Closing price
    return None


# Route for the stocks page
@app.route('/stocks', methods=['GET', 'POST'])
def stocks():
    if request.method == 'POST':
        symbol = request.form['symbol']
        data = fetch_stock_data(symbol)
        return render_template('stocks.html', symbol=symbol, data=data)
    else:
        return render_template('stocks.html')


# Route for get stocks symbols
@app.route('/get-stock-symbols')
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


# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle user registration
        username = request.form['username']
        password = request.form['password']

        # Save user data to the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="abhi992744",
            database="tradeplay_credentials"
        )
        cursor = conn.cursor()
        
        # Check if the username is already taken
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return render_template('register.html', message='Username already taken. Please choose another.')

        # Insert user data
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()

        # Insert initial balance into portfolio table
        cursor.execute('INSERT INTO portfolio (username) VALUES (%s)', (username,))
        conn.commit()
        conn.close()

        # Redirect to the login page after successful registration
        return redirect(url_for('login'))

    return render_template('register.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle user login
        username = request.form['username']
        password = request.form['password']

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="abhi992744",
            database="tradeplay_credentials"
            )
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            session['username'] = username  # Store username in session
            return redirect(url_for('index'))
        else:
            # Display an error message
            return render_template('login.html', message='Invalid username or password. Please try again.')
            
    return render_template('login.html')


# Route for logging out
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# Route for buying and selling stocks
@app.route('/buy-sell', methods=['GET', 'POST'])
def buy_sell():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get form data
        symbol = request.form['stock']
        quantity = int(request.form['quantity'])
        action = request.form['action']
        username = session['username']

        # Connect to the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="abhi992744",
            database="tradeplay_credentials"
        )
        cursor = conn.cursor()

        try:
            # Fetch stock price at the specified date
            stock_price = fetch_current_price(symbol)
            print(stock_price)
            if stock_price is None:
                raise Exception(f"Unable to fetch stock price for symbol {symbol}")

            # Fetch user's balance
            cursor.execute('SELECT balance FROM users WHERE username = %s', (username,))
            balance = cursor.fetchone()[0]
            print(balance)
            
            # Calculate transaction value
            transaction_value = quantity * stock_price
            print(transaction_value)
            
            if action == 'buy':
                # Check if user has sufficient balance
                if balance < transaction_value:
                    return render_template('buy_sell.html', error='Insufficient balance')

                # Check if the user already has this share in the portfolio
                cursor.execute('SELECT * FROM portfolio WHERE username = %s AND stock = %s', (username, symbol))
                existing_row = cursor.fetchone()

                if existing_row:
                    # Update the existing row in the portfolio table
                    cursor.execute('UPDATE portfolio SET quantity = quantity + %s, total_value = total_value + %s WHERE username = %s AND stock = %s',
                                   (quantity, transaction_value, username, symbol))
                else:
                    # Insert a new row in the portfolio table
                    cursor.execute('INSERT INTO portfolio (username, stock, quantity, price, total_value, action) VALUES (%s, %s, %s, %s, %s, %s)',
                                   (username, symbol, quantity, stock_price, transaction_value, action))
                    
                # Fetch user's balance
                cursor.execute('SELECT balance FROM users WHERE username = %s', (username,))
                balance = cursor.fetchone()[0]
                print(balance)
                
                # Update user's balance
                #new_balance = balance - transaction_value
                #cursor.execute('UPDATE users SET balance = %s WHERE username = %s', (new_balance, username))
                conn.commit()

            elif action == 'sell':
                # Check if user has sufficient stock quantity
                cursor.execute('SELECT quantity FROM portfolio WHERE username = %s AND stock = %s', (username, symbol))
                row = cursor.fetchone()
                if not row or row[0] < quantity:
                    return render_template('buy_sell.html', error='Insufficient stock quantity')

                # Update balance and portfolio table for sell action
                #new_balance = balance + transaction_value
                #cursor.execute('UPDATE users SET balance = %s WHERE username = %s', (new_balance, username))
                cursor.execute('UPDATE portfolio SET quantity = quantity - %s WHERE username = %s AND stock = %s',
                               (quantity, username, symbol))
                conn.commit()

            # Insert transaction data into transactions table
            cursor.execute('''
                INSERT INTO transactions (username, stock, quantity, price, total_value, action)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (username, symbol, quantity, stock_price, transaction_value, action))
            conn.commit()
            return redirect(url_for('portfolio'))

        except Exception as e:
            # Handle any exceptions
            conn.rollback()
            return render_template('buy_sell.html', error=str(e))

        finally:
            # Close cursor and connection
            cursor.close()
            conn.close()

    return render_template('buy_sell.html')



# Route for the portfolio page
@app.route('/portfolio')
def portfolio():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Retrieve user's portfolio data from the database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="abhi992744",
        database="tradeplay_credentials"
    )
    cursor = conn.cursor()
    username = session['username']
    cursor.execute('SELECT stock, SUM(quantity) AS total_quantity, AVG(price) AS average_price, SUM(total_value) AS total_value FROM portfolio WHERE username = %s GROUP BY stock', (username,))
    portfolio = cursor.fetchall()
    conn.close()

    return render_template('portfolio.html', portfolio=portfolio)


@app.route('/transaction-history')
def transaction_history():
    if 'username' in session:
        # Retrieve user's transaction history from the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="abhi992744",
            database="tradeplay_credentials"
        )
        cursor = conn.cursor()
        username = session['username']
        cursor.execute('SELECT * FROM transactions WHERE username = %s ORDER BY transaction_time DESC', (username,))
        transaction_history = cursor.fetchall()
        conn.close()

        return render_template('transaction_history.html', transaction_history=transaction_history)
    else:
        return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)