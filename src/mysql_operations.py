import os  # Import the os module
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

MYSQL_URL = os.getenv('MYSQL_URL')
import pymysql

# Database connection setup
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="laravel_vue_shadcn",
        cursorclass=pymysql.cursors.DictCursor,
    )

# Insert a row
def insert_row(data):
    # event_time, event_flags, 
    # data["event_time"], data["event_flags"], 
    query = """
    INSERT INTO greeks (event_symbol, `index`, `time`, sequence, price, volatility, delta, gamma, theta, rho, vega)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        data["event_symbol"], data["index"], 
        data["time"], data["sequence"], data["price"], data["volatility"], 
        data["delta"], data["gamma"], data["theta"], data["rho"], data["vega"]
    )
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, values)
            conn.commit()

# def insert_row(data):
#     query = """
#     INSERT INTO greeks (
#         event_symbol, event_time, event_flags, `index`, `time`, sequence, 
#         price, volatility, delta, gamma, theta, rho, vega
#     )
#     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """
#     values = (
#         data["event_symbol"], data["event_time"], data["event_flags"], data["index"], 
#         data["time"], data["sequence"], data["price"], data["volatility"], 
#         data["delta"], data["gamma"], data["theta"], data["rho"], data["vega"]
#     )
    
#     try:
#         connection = get_connection()
#         with connection.cursor() as cursor:
#             cursor.execute(query, values)
#         connection.commit()
#     finally:
#         connection.close()            

# Insert or Update (Upsert) a row
def upsert_row(data):
    query = """
    INSERT INTO greeks (event_symbol, event_time, event_flags, `index`, `time`, sequence, price, volatility, delta, gamma, theta, rho, vega)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        event_time = VALUES(event_time),
        event_flags = VALUES(event_flags),
        `index` = VALUES(`index`),
        `time` = VALUES(`time`),
        sequence = VALUES(sequence),
        price = VALUES(price),
        volatility = VALUES(volatility),
        delta = VALUES(delta),
        gamma = VALUES(gamma),
        theta = VALUES(theta),
        rho = VALUES(rho),
        vega = VALUES(vega)
    """
    values = (
        data["event_symbol"], data["event_time"], data["event_flags"], data["index"], 
        data["time"], data["sequence"], data["price"], data["volatility"], 
        data["delta"], data["gamma"], data["theta"], data["rho"], data["vega"]
    )
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, values)
            conn.commit()

# Read rows based on a filter
def read_rows(delta_filter):
    query = "SELECT * FROM greeks WHERE delta >= %s"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (delta_filter,))
            rows = cursor.fetchall()
    return rows

def truncate_table(table_name='greeks'):
    """
    Truncate the specified table.
    :param table_name: Name of the table to truncate.
    """
    query = f"TRUNCATE TABLE greeks"
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
        connection.commit()
        print(f"Table '{table_name}' has been truncated.")
    except Exception as e:
        print(f"Error truncating table '{table_name}': {e}")
    finally:
        connection.close()

# Function to save or update greeks data in MySQL
async def save_greeks_to_mysql(greeks_data):
    del greeks_data["event_time"]
    del greeks_data["event_flags"]
    insert_row(greeks_data)

def get_event_symbols(conn):
    """
    Fetch all values of the 'event_symbol' field from the 'greeks' table.
    :return: List of event_symbol values.
    """
    query = "SELECT event_symbol FROM greeks;"
    
    try:
        # with get_connection() as conn:
        with conn.cursor() as cursor:
            # Execute the query
            cursor.execute(query)
            # Fetch all rows
            rows = cursor.fetchall()
            # Extract the event_symbol values into a list
            result = [row["event_symbol"] for row in rows]
            
        return result
    except Exception as e:
        print(f"Error fetching event_symbol values: {e}")
        return []
    # finally:
    #     conn.close()

def update_quote(connection, quote):
    query = """
    UPDATE option_chains
    SET bid_price = %s, ask_price = %s, bid_size = %s, ask_size = %s
    WHERE streamer_symbol = %s;
    """
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (quote.bid_price, quote.ask_price, quote.bid_size, quote.ask_size, quote.event_symbol))
        connection.commit()
        # print(f"Updated greeks for event_symbol '{event_symbol}'.")
    except Exception as e:
        print(f"Error updating greeks for streamer_symbol '{quote.event_symbol}': {e}")


# Example usage
# row_data = {
#     "event_symbol": ".TSLA250221P355",
#     "event_time": 0,
#     "event_flags": 0,
#     "index": 7461053953849950208,
#     "time": 1737161994421,
#     "sequence": 0,
#     "price": 0,
#     "volatility": 0,
#     "delta": 0.167,
#     "gamma": 0,
#     "theta": 0,
#     "rho": 0,
#     "vega": 0
# }

# # Insert
# insert_row(row_data)

# # Upsert
# upsert_row(row_data)

# # Read rows with delta >= 0.1
# rows = read_rows(0.1)
# for row in rows:
#     print(row)