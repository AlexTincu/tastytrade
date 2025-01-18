import asyncio
from datetime import date
from dataclasses import dataclass
from tastytrade import DXLinkStreamer
from tastytrade.instruments import get_option_chain
from tastytrade.dxfeed import Greeks, Quote
from tastytrade.utils import today_in_new_york
from tastytrade import Session
from tastytrade.instruments import OptionType
from tastytrade.instruments import Option

import os  # Import the os module
from dotenv import load_dotenv

@dataclass
class LivePrices:
    quotes: dict[str, Quote]
    greeks: dict[str, Greeks]
    streamer: DXLinkStreamer
    puts: list[Option]
    calls: list[Option]

    @classmethod    
    async def create(
        cls,
        session: Session,
        symbol: str = 'SPY',
        expiration: date = today_in_new_york()
    ):
        chain = get_option_chain(session, symbol)
        options = [o for o in chain[expiration]]
        # the `streamer_symbol` property is the symbol used by the streamer
        streamer_symbols = [o.streamer_symbol for o in options]

        streamer = await DXLinkStreamer(session)
        # subscribe to quotes and greeks for all options on that date
        await streamer.subscribe(Quote, [symbol] + streamer_symbols)
        await streamer.subscribe(Greeks, streamer_symbols)

        puts = [o for o in options if o.option_type == OptionType.PUT]
        calls = [o for o in options if o.option_type == OptionType.CALL]
        self = cls({}, {}, streamer, puts, calls)

        t_listen_greeks = asyncio.create_task(self._update_greeks())
        t_listen_quotes = asyncio.create_task(self._update_quotes())
        asyncio.gather(t_listen_greeks, t_listen_quotes)

        # wait we have quotes and greeks for each option
        while len(self.greeks) != len(options) or len(self.quotes) != len(options):
            await asyncio.sleep(0.1)

        return self

    async def _update_greeks(self):
        async for e in self.streamer.listen(Greeks):
            self.greeks[e.event_symbol] = e
            # print(e)   

    async def _update_quotes(self):
        async for e in self.streamer.listen(Quote):
            self.quotes[e.event_symbol] = e
            # print(e)           


load_dotenv()  # Load environment variables from .env file

# Set delta range (for example, between 0.2 and 0.8)
min_delta = float(os.getenv('MIN_DELTA', 0.16))
max_delta = float(os.getenv('MAX_DELTA', 0.22))

# Use environment variables for sensitive information
username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')
session = Session(username, password)

async def main(session):
    live_prices = await LivePrices.create(session, 'SPY', date(2025, 1, 17))
    # print(live_prices.quotes, live_prices.greeks)            

    # symbol = live_prices.calls[1].streamer_symbol
    # print(live_prices.quotes[symbol], live_prices.greeks[symbol])            

asyncio.run(main(session))