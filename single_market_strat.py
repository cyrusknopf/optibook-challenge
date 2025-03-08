from optibook.synchronous_client import Exchange
from optibook import common_types as t
from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from optibook.exchange_responses import InsertOrderResponse

def single_market_strat(exchange):
    INSTRUMENT_ID = "AMD"
    SPREAD_BUFFER = 0.01   # Place orders 2 cents away from mid-price
    ORDER_VOLUME = 5       # Number of shares per order
        
    # Function to get mid-price
    def get_mid_price(order_book):
        best_bid = order_book.bids[0].price if order_book.bids else None
        best_ask = order_book.asks[0].price if order_book.asks else None
            
        if best_bid is None or best_ask is None:
            return None  # Market isn't liquid enough
        return (best_bid + best_ask) / 2

    # Function to cancel all outstanding orders
    def cancel_all_orders(instrument_id):
        exchange.delete_orders(instrument_id)

    # Step 1: Get the latest order book
    order_book = exchange.get_last_price_book(INSTRUMENT_ID)
    mid_price = get_mid_price(order_book)

    if mid_price is None:
        print("Market data unavailable. Skipping this iteration.")
        return

    # Step 2: Calculate bid and ask prices
    bid_price = round(mid_price - SPREAD_BUFFER, 2)
    ask_price = round(mid_price + SPREAD_BUFFER, 2)

    # Step 3: Cancel existing orders if market moved significantly
    cancel_all_orders(INSTRUMENT_ID)
        
    print(exchange.get_outstanding_orders(INSTRUMENT_ID))

    # Step 4: Place new limit orders
    if bid_price != ask_price:
        bid_order = exchange.insert_order(
            INSTRUMENT_ID, price=bid_price, volume=ORDER_VOLUME,
            side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)

        ask_order = exchange.insert_order(
            INSTRUMENT_ID, price=ask_price, volume=ORDER_VOLUME,
            side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)

        print_order_response(bid_order)
        print_order_response(ask_order)
        
    else:
        print("Would have lead to a self, trade (skipping)")
        
def print_order_response(order_response: InsertOrderResponse):
    if order_response.success:
        print(f"Inserted order successfully, order_id='{order_response.order_id}'")
    else:
        print(f"Unable to insert order with reason: '{order_response.success}'")