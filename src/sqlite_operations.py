import sqlite3
import json

sqlitedb = '../sqlite/db.db'

def save_greeks_to_sqlite(data):
    """Save greeks data to SQLite database."""
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(sqlitedb)
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS greeks (
            event_symbol TEXT PRIMARY KEY,
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

    # Insert or update data into the table
    cursor.execute('''
        INSERT INTO greeks (
            event_symbol, event_time, event_flags, "index", time, sequence,
            price, volatility, delta, gamma, theta, rho, vega
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(event_symbol) DO UPDATE SET
            event_time=excluded.event_time,
            event_flags=excluded.event_flags,
            "index"=excluded."index",
            time=excluded.time,
            sequence=excluded.sequence,
            price=excluded.price,
            volatility=excluded.volatility,
            delta=excluded.delta,
            gamma=excluded.gamma,
            theta=excluded.theta,
            rho=excluded.rho,
            vega=excluded.vega
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
    """Read greeks data from SQLite database."""
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
