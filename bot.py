from optibook.synchronous_client import Exchange
from optibook import common_types as t
from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from optibook.exchange_responses import InsertOrderResponse

import time
import json

from collections import defaultdict

import z_score_single_market_arbitrage as zss
import single_market_strat as sms

TOTAL_POS_LIM : int = 750
OUTS_LIM : int  = 1000
NUM_TRADES_TO_SAVE = 150
TICKERS = ["AMD", "ASML", "NVDA", "SEMIS_ETF_EU", "SEMIS_ETF_US"]

class Bot():
    # The number of sell orders currently for each ticket
    pos_sell : dict[str, int]
    # The number of buy orders currently for each ticket
    pos_buy : dict[str, int]

    def __init__(self):
        # Saves previous n trades for each instrument
        '''
        self.AMD_data = []
        self.ASML_data = []
        self.NVDA_data = []
        self.ETF_EU_data = []
        self.ETF_US_data = []
        '''
        self.data = defaultdict(list)
        
        self.tick_count = 0
        
        # Setup the exchange
        self.exchange = Exchange()
        _ = self.exchange.connect()

    def run_bot(self):
        while True:
            for ticker in TICKERS:
                if not self.check_markets_open(ticker):
                    pass
                
                self.data[ticker] = zss.save_current_data_to_logs(NUM_TRADES_TO_SAVE, ticker, self.data[ticker], self.exchange)
                
                try:
                    current_data = self.exchange.get_last_price_book(ticker).asks[0].price
                    zss.use_z_score(self.data[ticker], current_data, ticker, self.exchange)
                except:
                    pass
                
            time.sleep(0.5)
                
            #current_data = self.exchange.get_last_price_book("AMD").asks[0].price
            #zss.use_z_score(self.AMD_data, current_data, "AMD", self.exchange)
            
            #sms.single_market_strat(self.exchange)

    def check_markets_open(self, market: str):
        if self.exchange.get_instruments()[market].paused:
            return False
        else:
            return True

    def run_batch() -> ... :
        ...

    
    def check_pos_lim(self, want : int, position : int, is_buy : bool) -> int:
        '''
        Ensure we do not attempt to purchase an ammount
        of an instrument that makes us exceeds 750 units
        of that instrument.
        Returns the maximum number of purchasable instruments
        which keeps us within the limit
        
        @position: position for instrument of interest
        '''
        if want < 0:
            return 0
        if is_buy:
            purchasable = TOTAL_POS_LIM - position
            return min(purchasable, want)
        else:
            sellable = TOTAL_POS_LIM + position
            return min(sellable, want)

    
    def check_outs_lim(self, want : int, instr : str) -> int:
        '''
        @want : volume we want to buy/sell
        @instr : instrument to buy/sell
        @returns : largest possible number to buy/sell less than or equal to want
        '''
        orders : dict[int, t.OrderStatus] = self.exchange.get_outstanding_orders(instr)

        total_volume = sum(order.volume for order in orders.values()) # fuck std lib functions

        return min(want, OUTS_LIM - total_volume)
    
    def check_lims(self, want : int, instr : str, position : int, is_buy : bool):
        vol : int = 0
        vol = self.check_pos_lim(want, position, is_buy)
        vol = self.check_outs_lim(want, instr)
        return vol
    
    def check_comb_hedge(self):
        ...

    def chunk() -> ... :
        ...

    def order() -> ... :
        ...
    
    """def print_report(self, e: Exchange):
        pnl = e.get_pnl()
        positions = e.get_positions()
        my_trades = e.poll_new_trades(BASKET_INSTRUMENT_ID)
        all_market_trades = e.poll_new_trade_ticks(BASKET_INSTRUMENT_ID)
        print(f'I have done {len(my_trades)} trade(s) in {BASKET_INSTRUMENT_ID} since the last report. There have been {len(all_market_trades)} market trade(s) in total in {BASKET_INSTRUMENT_ID} since the last report.')
        print(f'My PNL is: {pnl:.2f}')
        print(f'My current positions are: {json.dumps(positions, indent=3)}')
"""
    def print_order_response(self, order_response: InsertOrderResponse):
        if order_response.success:
            print(f"Inserted order successfully, order_id='{order_response.order_id}'")
        else:
            print(f"Unable to insert order with reason: '{order_response.success}'")
        
    def check_instrument_tradable(instrument_id: str, exchange) -> bool:
        if exchange.get_last_price_book(instrument_id).bids == [] or exchange.get_last_price_book(instrument_id).asks == []:
            print(f"Instrument {instrument_id} is not tradable")
            return False
        else:
            print(f"Instrument {instrument_id} is tradable")
            return True

    def reset_positions(self):
        # DO NOT RUN THIS FUNCTION OUTSIDE PRACTICE SESSIONS
        # This will reset all your positions

        # if not self.check_etfs_open():
        #     return False
        
        positions = self.exchange.get_positions()
        for instrument_id, position in positions.items():
            self.exchange.get_outstanding_orders(instrument_id)
            
if __name__ == '__main__':
    bot = Bot()
    
    while True:
        time.sleep(1.2)
        try:
            bot.run_bot()

        except Exception as e:
            print(f"There was an error, {e} restarting")
            bot = Bot()
            