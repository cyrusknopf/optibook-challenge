from optibook import *
from main.algorithms.base import BaseAlgorithm
from main.utils.iteration_data import IterationData
from main.constants import ETF_DIFFERENCE_THRESHOLD, BUY_X_STOCKS_EACH_ON_BASKET_OPPORTUNITY
from enum import Enum, auto
from time import sleep

class DualListingTradeOutcome(Enum):
    USUndervalued = auto()
    NoOpportunity = auto()
    USOvervalued = auto()

class DualListingAlgorithm(BaseAlgorithm):
    needs_stock_data = False
    
    def find_dual_listing_trade_opportunity(self, iteration_data: IterationData) -> DualListingTradeOutcome:
        """
        See if one ETF is much cheaper one one market than the other.
        """
        # Get the ETF and the individual stocks
        price_etf_us = iteration_data.price_book_for_etf("US")
        price_etf_eu = iteration_data.price_book_for_etf("EU")

        # check if the ETF is undervalued
        highest_etf_bid_us = max(price_etf_us.bids, key=lambda x: x.price)
        highest_etf_bid_eu = max(price_etf_eu.bids, key=lambda x: x.price)

        lowest_etf_ask_us = min(price_etf_us.asks, key=lambda x: x.price)
        lowest_etf_ask_eu = min(price_etf_eu.asks, key=lambda x: x.price)

        # print(f"ETF US: bid: {round(highest_etf_bid_us.price, 2)} ask: {round(lowest_etf_ask_us.price, 2)} ETF EU: bid: {round(highest_etf_bid_eu.price, 2)} ask: {round(lowest_etf_ask_eu.price, 2)}")
        if highest_etf_bid_us.price - lowest_etf_ask_eu.price > ETF_DIFFERENCE_THRESHOLD:
            return DualListingTradeOutcome.USUndervalued
        elif highest_etf_bid_eu.price - lowest_etf_ask_us.price > ETF_DIFFERENCE_THRESHOLD:
            return DualListingTradeOutcome.USOvervalued
        else:
            return DualListingTradeOutcome.NoOpportunity

    def handle_wrongly_valued_etf(self, outcome: DualListingTradeOutcome, iteration_data: IterationData):
        """
        If the ETFs are wrongly valued, buy the cheaper one and sell the more expensive one.
        """
        buy = "US" if outcome == DualListingTradeOutcome.USUndervalued else "EU"
        sell = "EU" if outcome == DualListingTradeOutcome.USUndervalued else "US"

        # Cancel outstanding BID orders
        for order_id, order_status in self.exchange.get_outstanding_orders("SEMIS_ETF_" + sell).items():
            if order_status.side == "bid":
                self.bot.broker.delete_order(sell, order_id)
      
        stock_position = iteration_data.position_for_asset("SEMIS_ETF_" + sell)
        stock_bids = iteration_data.price_book_for_etf(sell).bids
        # Sell stocks at highest bid price to get rid of asap
        if stock_position > 0:
            self.bot.broker(
                "SEMIS_ETF_" + sell, 
                price=min(stock_bids, key=lambda x: x.price).price,
                volume=stock_position
            )

        # Buy ETF at the lowest ask price
        lowest_price = iteration_data.price_book_for_etf(buy).asks[0]
        self.bot.broker.buy(
            "SEMIS_ETF_" + buy, 
            price=lowest_price.price,
            volume=min(lowest_price.volume, BUY_X_STOCKS_EACH_ON_BASKET_OPPORTUNITY),
            iteration_data=iteration_data
        )
        sleep(0.1)

        # Sell ETF at (higher price - lower price) / 2
        # for order_id, order_status in self.exchange.get_outstanding_orders(buy).items():
        #     if order_status.side == "bid" and order_status.instrument_id == buy:
        #         return # Other algo must think it is a good stock
        print("Uhhh")
        highest_price = iteration_data.price_book_for_etf(sell).bids[0]
        self.bot.broker.sell(
            "SEMIS_ETF_" + buy, 
            price=(highest_price.price + lowest_price.price) / 2,
            volume=min(lowest_price.volume, BUY_X_STOCKS_EACH_ON_BASKET_OPPORTUNITY),
            iteration_data=iteration_data
        )


    def run(self, iteration_data: IterationData):
        """"
        Performs dual listing trading.

        In dual listing trading, ETF prices are projected to predict the prices of t
        he individual stocks in the ETF and the other way around.

        The algo will buy stocks if the ETF values them higher than they are (and sell the ETF if in possession)
        as well as buying the ETF if the stocks are valued higher than the ETF (and selling the stocks if in possession)
        """
        if (
            not iteration_data.price_book_for_etf("US").bids or 
            not iteration_data.price_book_for_etf("EU").bids or
            not iteration_data.price_book_for_etf("US").asks or
            not iteration_data.price_book_for_etf("EU").asks
        ):
            return # Both need to be unpaused
        try:
            outcome = self.find_dual_listing_trade_opportunity(iteration_data)
            if outcome != DualListingTradeOutcome.NoOpportunity:
                self.handle_wrongly_valued_etf(outcome, iteration_data)
        except (IndexError, KeyError) as e: #, capnp.lib.capnp.KjException) as e: # likely code running too long after a check on if you can do X
            print("Error in basket trading: " + str(e))
        # except ValueError:
        #     print("Skipped iteration due to ETF data being unavailable...")