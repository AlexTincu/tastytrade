import os
from dotenv import load_dotenv
import json
import asyncio
from datetime import datetime, date

from tastytrade import Session
from tastytrade import Account
from decimal import Decimal

load_dotenv()  # Load environment variables from .env file

# symbols = ['AAPL', 'GOOGL', 'MSFT']  # Define a list of symbols

# Use environment variables for sensitive information
username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

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

async def main():
    """Retrieve and save account and position data to separate JSON files."""
    accounts = Account.get_accounts(session)

    filename = "../files/accounts.json"
    clean_file(filename)

    await save_accounts_to_file(accounts, filename)
    
    filename = "../files/positions.json"    
    clean_file(filename)

    for account in accounts:
        positions = account.get_positions(session)

        await save_positions_to_file(positions, filename)


# Run the async function using the event loop
if __name__ == "__main__":
    asyncio.run(main())