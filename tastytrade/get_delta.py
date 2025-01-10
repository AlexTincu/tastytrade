from tastytrade import Session
from tastytrade import Account

from tastytrade import DXLinkStreamer
from tastytrade.dxfeed import Greeks
from tastytrade.instruments import get_option_chain
from tastytrade.utils import get_tasty_monthly

import json
import asyncio
from decimal import Decimal  # Add this import

symbol = 'AAPL'
filename="greeks_data.json"

session = Session('macovei17', 'gujco5-pinsuK-tespuw')

# account = Account.get_accounts(session)[0]
# positions = account.get_positions(session)
# print(positions[0])

def clean_file(filename="greeks_data.json"):
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

async def save_greeks_to_file(data, filename="greeks_data.json"):
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

    # Clean the file before appending new data
    clean_file(filename)
    
    chain = get_option_chain(session, symbol)
    exp = get_tasty_monthly()  # 45 DTE expiration!
    # subs_list = [chain[exp][0].streamer_symbol]
    # subs_list = ['.AAPL250110C110', '.AAPL250221C370']

    # Collect streamer symbols for all items in chain[exp]
    # Filter items by days_to_expiration and collect their streamer_symbol
    subs_list = [
        item.streamer_symbol
        for item in chain[exp]
        # if item.days_to_expiration <= 20
    ]
    
    async with DXLinkStreamer(session) as streamer:
        # Subscribe to Greeks for all items in subs_list
        await streamer.subscribe(Greeks, subs_list)
        
        processed_count = 0  # Track the number of processed items
        total_items = len(subs_list)  # Total items to process

        # Continuously process incoming events
        print("Starts for:", symbol)
        # print("Subscribed to symbols:", subs_list)                
        # while True:
        while processed_count < total_items:
            greeks = await streamer.get_event(Greeks)  # Get the next event
            # print(greeks)  # Print the update
            await save_greeks_to_file(greeks)  # Save the data to a JSON file
            
            # Increment the count if the event belongs to subs_list
            if greeks.event_symbol in subs_list:
                processed_count += 1
        
        print("Done")

# Run the async function using the event loop
if __name__ == "__main__":
    asyncio.run(main())    