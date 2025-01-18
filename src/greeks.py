import os  # Import the os module
from dotenv import load_dotenv
import json
import asyncio
import sqlite3
import csv
from decimal import Decimal
from datetime import datetime, date

from tastytrade import Session
from tastytrade import DXLinkStreamer
from tastytrade.dxfeed import Greeks
from tastytrade.dxfeed import Quote
from tastytrade.instruments import get_option_chain
from tastytrade.utils import get_tasty_monthly

# from tortoise import Tortoise, run_async
# from tortoise import run_async
# from sqlite_operations import save_greeks_to_sqlite, read_greeks_from_db
from mysql_operations import save_greeks_to_mysql, truncate_table, get_event_symbols, get_connection, update_quote

load_dotenv()  # Load environment variables from .env file

filename="../files/greeks/greeks.json"

# Set delta range (for example, between 0.2 and 0.8)
min_delta = float(os.getenv('MIN_DELTA', 0.16))
max_delta = float(os.getenv('MAX_DELTA', 0.22))

# Use environment variables for sensitive information
username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

sqlitedb = '../sqlite/db.db'

session = Session(username, password)

def get_watchlist_symbols():
    with open('../files/watchlist.json', 'r') as file:
        watchlist = json.load(file)
    return [item['symbol'] for item in watchlist if 'symbol' in item]    

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
    
    if (1 - max_delta) <= data.delta <= (1 - min_delta):
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

def convert_greeks_from_json_to_csv(json_filename, csv_filename):
    print("Starts exporting options to csv")
    clean_file('../files/greeks/greeks.csv')

    """Read greeks data from a JSON file and save it to a CSV file."""
    try:
        with open(json_filename, 'r') as json_file:
            greeks_data = json.load(json_file)

        with open(csv_filename, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Write the header
            writer.writerow(['root_symbol', 'date', 'strike_price', 'event_symbol', 'delta'])

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

                # Map option_type to "PUT" or "CALL"
                # option_type_mapped = "PUT" if option_type == "P" else "CALL"

                # Write the row to the CSV
                writer.writerow([root_symbol, human_readable_date, strike_price, item['event_symbol'], delta])

        print(f"Data has been successfully written to {csv_filename}.")
        
    except Exception as e:
        print(f"Error saving data to CSV: {e}")


# Function to round greeks data
def round_greeks_data(item):
    return {
        "event_symbol": item["event_symbol"],
        "event_time": item["event_time"],
        "event_flags": item["event_flags"],
        "index": item["index"],
        "time": item["time"],
        "sequence": item["sequence"],
        "price": round(item["price"], 3),
        "volatility": round(item["volatility"], 3),
        "delta": round(item["delta"], 3),
        "gamma": round(item["gamma"], 3),
        "theta": round(item["theta"], 3),
        "rho": round(item["rho"], 3),
        "vega": round(item["vega"], 3),
    }

def transform_call_to_put(item):
    # it is a CALL
    if item["delta"] <= max_delta:
        return item

    # it's a PUT
    call_symbol = item["event_symbol"]    
    parts = call_symbol.rsplit("C", 1) # Split the string into two parts: everything before the last occurrence and the last occurrence onward    
    put_symbol = "P".join(parts) # Reconstruct the string with the replacement

    return {
        "event_symbol": put_symbol,
        "event_time": item["event_time"],
        "event_flags": item["event_flags"],
        "index": item["index"],
        "time": item["time"],
        "sequence": item["sequence"],
        "price": 0,
        "volatility": 0,
        "delta": round(1 - item["delta"], 3),
        "gamma": 0,
        "theta": 0,
        "rho": 0,
        "vega": 0,
    }

# Function to save or update greeks data in MySQL
# async def save_greeks_to_mysql(greeks_data):
#     for item in greeks_data:
#         await Greeks.update_or_create(
#             defaults=item,
#             event_symbol=item["event_symbol"]
#         )

# symbols = ['AAPL', 'GOOGL', 'MSFT']  # Define a list of symbols

async def fetch_quotes():
    connection = get_connection()

    subs_list = get_event_symbols(connection)
    
    try:
        async with DXLinkStreamer(session) as streamer:
            await streamer.subscribe(Quote, subs_list)
            # quotes = {}
            quotes = 0
            async for quote in streamer.listen(Quote):
                # array = serialize_object(quote)
                update_quote(connection, quote)
                # print(f"Done for {quote.event_symbol}")
                # quotes[quote.event_symbol] = array
                quotes = quotes + 1
                # if len(quotes) >= len(subs_list):
                if quotes >= len(subs_list):
                    break
            
            print(f"{quotes} quotes updated.")
    finally:        
        connection.close() # Close the shared connection after all calls

async def fetch_greeks():
    symbols = get_watchlist_symbols()
    # Clean the file before appending new data
    # clean_file(filename)
    truncate_table()

    for symbol in symbols:  # Iterate over each symbol
        # Update the filename for each symbol
        # filename = f"../files/greeks/{symbol}.json"
        # clean_file(filename)
        
        chain = get_option_chain(session, symbol)
        exp = get_tasty_monthly()  # 45 DTE expiration!

        # Collect streamer symbols for all items in chain[exp]
        subs_list = [
            item.streamer_symbol
            for item in chain[exp]
        ]
        
        async with DXLinkStreamer(session) as streamer:
            # Subscribe to Greeks for all items in subs_list
            await streamer.subscribe(Greeks, subs_list)
            
            # Continuously process incoming events
            print("Starts for:", symbol)
            for _ in subs_list:  # Use a for loop to iterate over subs_list
                greeks = await streamer.get_event(Greeks)  # Get the next event                        
                
                # Check if delta is within the specified range
                if filter_by_delta(greeks, min_delta, max_delta):     
                    greeks = serialize_object(greeks)
                    greeks = round_greeks_data(greeks)
                    greeks = transform_call_to_put(greeks)
                    # print(greeks)
                    # await save_greeks_to_file(greeks, filename)  # Save the data to a JSON file                    
                    # save_greeks_to_sqlite(greeks)
                    await save_greeks_to_mysql(greeks)
                    # print(greeks)  # Print the update
                    
            print(f"Done for {symbol}")

async def main():
    # await mysql_init()  # Initialize the ORM
    await fetch_greeks()
    await fetch_quotes()
    # convert_greeks_from_json_to_csv("../files/greeks/greeks.json",'../files/greeks/greeks.csv')    

# Run the async function using the event loop
if __name__ == "__main__":
    asyncio.run(main())
    # run_async(main())