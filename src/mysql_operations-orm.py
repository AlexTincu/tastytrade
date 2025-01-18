from tortoise import Tortoise
from models import OptionsGreeks
import os  # Import the os module
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

MYSQL_URL = os.getenv('MYSQL_URL')

async def mysql_init():
    await Tortoise.init(
        db_url=MYSQL_URL,  # Update with your MySQL credentials
        modules={
            'models': ['models']  # Specify the module where your models are defined
        }
    )
    await Tortoise.generate_schemas(safe=True)  # Safe=True avoids overwriting existing tables
    

async def save_greeks_to_mysql(rounded_data):
    # for rounded_data in greeks_data:
    del rounded_data["event_time"]
    del rounded_data["event_flags"]
    await OptionsGreeks.create(
        defaults={
            # "event_time": rounded_data["event_time"],
            # "event_flags": rounded_data["event_flags"],
            "index": rounded_data["index"],
            "time": rounded_data["time"],
            "sequence": rounded_data["sequence"],
            "price": rounded_data["price"],
            "volatility": rounded_data["volatility"],
            "delta": rounded_data["delta"],
            "gamma": rounded_data["gamma"],
            "theta": rounded_data["theta"],
            "rho": rounded_data["rho"],
            "vega": rounded_data["vega"],
        },
        event_symbol=rounded_data["event_symbol"]
    )
