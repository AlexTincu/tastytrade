import os  # Import the os module
from dotenv import load_dotenv
import json
import asyncio

from tastytrade import Session
from tastytrade import Account
from tastytrade import DXLinkStreamer
from tastytrade.dxfeed import Greeks
from tastytrade.instruments import get_option_chain
from tastytrade.utils import get_tasty_monthly
from decimal import Decimal  # Add this import

load_dotenv()  # Load environment variables from .env file

# filename="../files/greeks_data.json"
symbols = ['AAPL', 'GOOGL', 'MSFT']  # Define a list of symbols

# Set delta range (for example, between 0.2 and 0.8)
min_delta = float(os.getenv('MIN_DELTA', 0.16))
max_delta = float(os.getenv('MAX_DELTA', 0.22))

# Use environment variables for sensitive information
username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

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

# Function to filter Greeks data based on delta value
def filter_by_delta(data, min_delta, max_delta):
    """Filter the Greeks data based on delta within a given range."""
    if min_delta <= data.delta <= max_delta:
        return True
    return False

async def save_greeks_to_file(data, filename):
    """Append the greeks data to a JSON file."""
    serialized_data = serialize_greeks(data)
    # print(serialized_data)
    
    try:
        # Load existing data if the file already exists
        try:
            with open(filename, "r") as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = []

        # Append the new data        
        existing_data.append(serialized_data)

        # Write updated data back to the file
        with open(filename, "w") as file:
            json.dump(existing_data, file, indent=4)

    except Exception as e:
        print(f"Error saving data to file: {e}")

async def main():
    for symbol in symbols:  # Iterate over each symbol
        # Update the filename for each symbol
        filename = f"../files/greeks/{symbol}.json"

        # Clean the file before appending new data
        clean_file(filename)
        
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
                    await save_greeks_to_file(greeks, filename)  # Save the data to a JSON file
                    # print(greeks)  # Print the update
                    
            print(f"Done for {symbol}")

# Run the async function using the event loop
if __name__ == "__main__":
    asyncio.run(main())    