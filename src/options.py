import os  # Import the os module
from dotenv import load_dotenv
import json
import asyncio
import sqlite3
import csv

from tastytrade import Session
from tastytrade import DXLinkStreamer
from tastytrade.dxfeed import Greeks
from tastytrade.instruments import get_option_chain
from tastytrade.utils import get_tasty_monthly
from decimal import Decimal
from datetime import datetime, date

load_dotenv()  # Load environment variables from .env file


def get_watchlist_symbols():
    with open('../files/watchlist.json', 'r') as file:
        watchlist = json.load(file)
    return [item['symbol'] for item in watchlist if 'symbol' in item]    

filename="../files/greeks/greeks.json"
# symbols = ['AAPL', 'GOOGL', 'MSFT']  # Define a list of symbols
symbols = get_watchlist_symbols()

# Set delta range (for example, between 0.2 and 0.8)
min_delta = float(os.getenv('MIN_DELTA', 0.16))
max_delta = float(os.getenv('MAX_DELTA', 0.22))

# Use environment variables for sensitive information
username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')
sqlitedb = '../sqlite/db.db'

session = Session(username, password)

# account = Account.get_accounts(session)[0]
# positions = account.get_positions(session)
# print(positions[0])

def clean_file(filename):
    """Clean the file by resetting its contents."""
    try:
        # Initialize the data storage
        existing_data = []

        # Write updated data back to the file
        with open(filename, "w") as file:
            json.dump(existing_data, file, indent=4)
            print(f"File {filename} has been cleaned.")
    except Exception as e:
        print(f"Error cleaning file: {e}")
        
def serialize_greeks(greeks_data):
    """Convert Greeks data into a JSON-serializable format."""
    def convert_value(value):
        if isinstance(value, Decimal):
            return float(value)  # Convert Decimal to float
        return value  # Return other types as-is

    return {
        key: convert_value(value)
        for key, value in vars(greeks_data).items()  # Convert Greeks object to a dictionary
    }

  
def serialize_object(data):
    """Convert data into a JSON-serializable format."""
    def convert_value(value):
        if isinstance(value, Decimal):
            return float(value)  # Convert Decimal to float
        elif isinstance(value, (datetime, date)):
            return value.isoformat()  # Convert datetime and date to ISO format string
        elif isinstance(value, list):
            return [convert_value(item) for item in value]  # Recursively convert list items
        elif isinstance(value, dict):
            return {key: convert_value(val) for key, val in value.items()}  # Recursively convert dict items
        else:
            return value  # Return other types as-is

    if hasattr(data, '__dict__'):
        return {key: convert_value(value) for key, value in vars(data).items()}
    elif isinstance(data, dict):
        return {key: convert_value(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_value(item) for item in data]
    else:
        return convert_value(data)
    
# Function to filter Greeks data based on delta value
def filter_by_delta(data, min_delta, max_delta):
    """Filter the Greeks data based on delta within a given range."""
    if min_delta <= data.delta <= max_delta:
        return True
    return False

async def save_greeks_to_file(data, filename):
    """Append the greeks data to a JSON file."""

    try:
        # Load existing data if the file already exists
        try:
            with open(filename, "r") as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = []

        # Append the new data        
        existing_data.append(data)

        # Write updated data back to the file
        with open(filename, "w") as file:
            json.dump(existing_data, file, indent=4)

    except Exception as e:
        print(f"Error saving data to file: {e}")

# does not work yet
def save_greeks_to_db(data):
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(sqlitedb)
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS greeks (
            event_symbol TEXT,
            event_time INTEGER,
            event_flags INTEGER,
            "index" INTEGER,
            time INTEGER,
            sequence INTEGER,
            price REAL,
            volatility REAL,
            delta REAL,
            gamma REAL,
            theta REAL,
            rho REAL,
            vega REAL
        )
    ''')

    # Insert data into the table
    cursor.execute('''
        INSERT INTO greeks (
            event_symbol, event_time, event_flags, "index", time, sequence,
            price, volatility, delta, gamma, theta, rho, vega
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['event_symbol'], data['event_time'], data['event_flags'], data['index'],
        data['time'], data['sequence'], data['price'], data['volatility'], data['delta'],
        data['gamma'], data['theta'], data['rho'], data['vega']
    ))

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

def read_greeks_from_db():
    # Connect to the SQLite database
    conn = sqlite3.connect(sqlitedb)
    cursor = conn.cursor()

    # Execute a query to select all data from the greeks table
    cursor.execute('SELECT * FROM greeks')

    # Fetch all rows from the executed query
    rows = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    # Return the fetched rows
    return rows

def parse_event_symbol(event_symbol):
    # Find the index where the first numerical character appears
    first_num_index = next(i for i, c in enumerate(event_symbol) if c.isdigit())
    
    # Extract the root symbol
    root_symbol = event_symbol[:first_num_index]
    
    # Extract the date (next 6 characters)
    date = event_symbol[first_num_index:first_num_index + 6]
    
    # Extract the type (P or C)
    option_type = event_symbol[first_num_index + 6]
    
    # Extract the strike price (everything after P or C)
    strike_price = event_symbol[first_num_index + 7:]
    
    return [root_symbol, date, option_type, strike_price]

def save_greeks_to_csv(json_filename, csv_filename):
    """Read greeks data from a JSON file and save it to a CSV file."""
    try:
        with open(json_filename, 'r') as json_file:
            greeks_data = json.load(json_file)

        with open(csv_filename, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Write the header
            writer.writerow(['root_symbol', 'date', 'option_type', 'strike_price', 'event_symbol', 'delta'])

            for item in greeks_data:
                # Parse the event_symbol
                root_symbol, date, option_type, strike_price = parse_event_symbol(item['event_symbol'])
                
                # Transform date from YYMMDD to YYYY-MM-DD
                year = '20' + date[:2]  # Assuming the year is in the 2000s
                month = date[2:4]
                day = date[4:6]
                human_readable_date = f"{year}-{month}-{day}"

                # Round delta to 2 decimal places
                delta = round(item['delta'], 2)

                # Write the row to the CSV
                writer.writerow([root_symbol, human_readable_date, option_type, strike_price, item['event_symbol'], delta])

        print(f"Data has been successfully written to {csv_filename}.")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")


async def main():
    # # Clean the file before appending new data
    # clean_file(filename)

    # for symbol in symbols:  # Iterate over each symbol
    #     # Update the filename for each symbol
    #     # filename = f"../files/greeks/{symbol}.json"
    #     # clean_file(filename)
        
    #     chain = get_option_chain(session, symbol)
    #     exp = get_tasty_monthly()  # 45 DTE expiration!

    #     # Collect streamer symbols for all items in chain[exp]
    #     subs_list = [
    #         item.streamer_symbol
    #         for item in chain[exp]
    #     ]
        
    #     async with DXLinkStreamer(session) as streamer:
    #         # Subscribe to Greeks for all items in subs_list
    #         await streamer.subscribe(Greeks, subs_list)
            
    #         # Continuously process incoming events
    #         print("Starts for:", symbol)
    #         for _ in subs_list:  # Use a for loop to iterate over subs_list
    #             greeks = await streamer.get_event(Greeks)  # Get the next event                        
                
    #             # Check if delta is within the specified range
    #             if filter_by_delta(greeks, min_delta, max_delta):     
    #                 greeks = serialize_object(greeks)
    #                 await save_greeks_to_file(greeks, filename)  # Save the data to a JSON file                    
    #                 save_greeks_to_db(greeks)
    #                 # print(greeks)  # Print the update
                    
    #         print(f"Done for {symbol}")

    print("Starts ")
    clean_file('../files/greeks/greeks.csv')

    save_greeks_to_csv("../files/greeks/greeks.json",'../files/greeks/greeks.csv')    
    print(f"Done")  

# Example usage
# greeks_data = read_greeks_from_db()
# for row in greeks_data:
#     print(row)    

# Run the async function using the event loop
# if __name__ == "__main__":
asyncio.run(main())