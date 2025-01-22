import os
from dotenv import load_dotenv
import json
import asyncio
from datetime import datetime, date

from tastytrade import Session
from tastytrade import Account
from tastytrade import Watchlist

from decimal import Decimal
from mysql_operations import save_watchlist_to_mysql, truncate_table, get_connection


load_dotenv()  # Load environment variables from .env file

# Use environment variables for sensitive information
username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')
watchlist_name = os.getenv('TASTYTRADE_WATCHLIST')

session = Session(username, password)

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

async def save_accounts_to_file(accounts, filename):
    """Save the serialized account data to a JSON file."""
    serialized_data = [serialize_object(account) for account in accounts]
    
    try:
        with open(filename, "w") as file:
            json.dump(serialized_data, file, indent=4)
    except Exception as e:
        print(f"Error saving account data to file: {e}")

async def save_positions_to_file(positions, filename):
    """Save the serialized position data to a JSON file."""
    serialized_data = [serialize_object(position) for position in positions]
    
    try:
        with open(filename, "w") as file:
            json.dump(serialized_data, file, indent=4)
    except Exception as e:
        print(f"Error saving position data to file: {e}")

async def save_watchlist_to_file(watchlist, filename):
    """Save the serialized watchlist data to a JSON file."""
    serialized_data = serialize_object(watchlist)
    
    try:
        with open(filename, "w") as file:
            json.dump(serialized_data, file, indent=4)
    except Exception as e:
        print(f"Error saving watchlist data to file: {e}")


async def main():
    path = './python_tastytrade/files/'
    """Retrieve and save account and position data to separate JSON files."""
    accounts = Account.get_accounts(session)

    # Save accounts to file
    filename = f"{path}/accounts.json"
    clean_file(filename)

    await save_accounts_to_file(accounts, filename)

    # Save watchlist to file    
    watchlist = Watchlist.get_private_watchlist(session, watchlist_name)

    # filename = f"{path}/watchlist.json"
    # clean_file(filename)
    # await save_watchlist_to_file(watchlist.watchlist_entries, filename)
    
    try:
        connection = get_connection()

        await truncate_table(watchlist)
        watchlist_entries = serialize_object(watchlist.watchlist_entries)
        await save_watchlist_to_mysql(watchlist_entries)

    finally:        
        connection.close() # Close the shared connection after all calls    
    

    # Save positions to file
    filename = f"{path}/positions.json"
    clean_file(filename)

    for account in accounts:
        positions = account.get_positions(session)

        await save_positions_to_file(positions, filename)


# Run the async function using the event loop
if __name__ == "__main__":
    asyncio.run(main())