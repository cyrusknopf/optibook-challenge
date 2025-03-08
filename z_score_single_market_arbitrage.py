from optibook.synchronous_client import Exchange
from optibook import common_types as t
from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from optibook.exchange_responses import InsertOrderResponse    
    
import datetime
import json
import statistics as s

def save_current_data_to_logs(NUM_TRADES_TO_SAVE: int, datastr: str, trade_data: list, exchange):
    """
    AMD = exchange.get_trade_tick_history("AMD")
    ASML = exchange.get_trade_tick_history("ASML")
    NVDA = exchange.get_trade_tick_history("NVDA")
    ETF_EU = exchange.get_trade_tick_history("SEMIS_ETF_EU")
    ETF_US = exchange.get_trade_tick_history("SEMIS_ETF_US")
     
    AMD_dict = [trade_tick_to_dict(tick) for tick in AMD]
    ASML_dict = [trade_tick_to_dict(tick) for tick in ASML]
    NVDA_dict = [trade_tick_to_dict(tick) for tick in NVDA]
    ETF_EU_dict = [trade_tick_to_dict(tick) for tick in ETF_EU]
    ETF_US_dict = [trade_tick_to_dict(tick) for tick in ETF_US]
        
    # Save data to files
    with open("AMD_data.txt", "a") as f:
        f.write(json.dumps(AMD_dict) + "\n")

    with open("ASML_data.txt", "a") as f:
        f.write(json.dumps(ASML_dict) + "\n")

    with open("NVDA_data.txt", "a") as f:
        f.write(json.dumps(NVDA_dict) + "\n")

    with open("ETF_EU_data.txt", "a") as f:
        f.write(json.dumps(ETF_EU_dict) + "\n")

    with open("ETF_US_data.txt", "a") as f:
        f.write(json.dumps(ETF_US_dict) + "\n")
    """
    #Adds current data to list
    try:
        current_price = exchange.get_last_price_book(datastr).asks[0].price
        len(trade_data)
    except:
        return []
    
    if datastr == "AMD":
        if len(trade_data) >= NUM_TRADES_TO_SAVE:
            trade_data = trade_data[1:NUM_TRADES_TO_SAVE]
        trade_data.append(current_price)
        return trade_data
    elif datastr == "ASML":
        if len(trade_data) >= NUM_TRADES_TO_SAVE:
            trade_data = trade_data[1:NUM_TRADES_TO_SAVE]
        return trade_data.append(exchange.get_last_price_book("ASML").asks[0].price)
    elif datastr == "NVDA":
        if len(trade_data) >= NUM_TRADES_TO_SAVE:
            trade_data = trade_data[1:NUM_TRADES_TO_SAVE]
        return trade_data.append(exchange.get_last_price_book("NVDA").asks[0].price)
    elif datastr == "ETF_EU":
        if len(trade_data) >= NUM_TRADES_TO_SAVE:
            trade_data = trade_data[1:NUM_TRADES_TO_SAVE]
        return trade_data.append(exchange.get_last_price_book("ETF_EU").asks[0].price)
    elif datastr == "ETF_US":
        if len(trade_data) >= NUM_TRADES_TO_SAVE:
            trade_data = trade_data[1:NUM_TRADES_TO_SAVE]
        return trade_data.append(exchange.get_last_price_book("ETF_US").asks[0].price)
    
    return []
        

def trade_tick_to_dict(trade_tick):
    return {
        'timestamp': trade_tick.timestamp.isoformat() if trade_tick.timestamp else None,
        'instrument_id': trade_tick.instrument_id,
        'price': trade_tick.price,
        'volume': trade_tick.volume,
        'aggressor_side': trade_tick.aggressor_side,
        'buyer': trade_tick.buyer,
        'seller': trade_tick.seller,
        'trade_id': trade_tick.trade_id
    }

def load_data_from_logs(filename):
    with open(filename, "r") as f:
        data = f.readlines()
        
    def dict_to_trade_tick(data):
        return TradeTick(
            timestamp=datetime.fromisoformat(data['timestamp']) if data['timestamp'] else None,
            instrument_id=data['instrument_id'],
            price=data['price'],
            volume=data['volume'],
            aggressor_side=data['aggressor_side'],
            buyer=data['buyer'],
            seller=data['seller'],
            trade_id=data['trade_id']
        )
        
    trade_ticks = []
    for line in data:
        trade_ticks.extend([dict_to_trade_tick(json.loads(item)) for item in json.loads(line)])
        
    return trade_ticks
    
def calculate_z_score(dataset: list, current_data: int):
    if len(dataset) <= 1:
        return 0
    
    mean = s.mean(dataset)
    sd = s.stdev(dataset)
    if sd == 0:
        return 0
        
    z_score = (current_data - mean)/sd
    return z_score
    
def use_z_score(trade_data, current_data: int, instrument_id: str, exchange):
    if trade_data == None: 
        return 0
    z_score = calculate_z_score(trade_data, current_data)
    if z_score > 2:
        try:
            bid_price = exchange.get_last_price_book(instrument_id).bids[0].price
        except:
            return
        
        positions = exchange.get_positions()
        bid_order = exchange.insert_order(
            instrument_id, price=bid_price, volume=5,
            side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)
        positions = exchange.get_positions()

    elif z_score < -2:
        try:
            ask_price = exchange.get_last_price_book(instrument_id).asks[0].price
        except:
            return
        
        positions = exchange.get_positions()
        ask_order = exchange.insert_order(
            instrument_id, price=ask_price, volume=5,
            side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)
        positions = exchange.get_positions()

        
''' 
def sell_positions(exchange):
    positions = exchange.get_positions()
    pnl = exchange.get_pnl()
    print(f'Positions before: {positions}')
    print(f'\nPnL before: {pnl:.2f}')
    
    try:
        min_sell_price = exchange.get_last_price_book("AMD").asks[0].price ** 0.9
    except:
        return
    
    print(f'\nTrading out of positions')
    for iid, pos in positions.items():
        if pos > 0:
            print(f'-- Inserting sell order for {pos} lots of {iid}, with limit price {min_sell_price:.2f}')
            exchange.insert_order(iid, price=min_sell_price, volume=pos, side='ask', order_type='ioc') 
        time.sleep(0.10)

    time.sleep(1.0)

    positions = exchange.get_positions()
    pnl = exchange.get_pnl()
    print(f'\nPositions after: {positions}')
    print(f'\nPnL after: {pnl:.2f}')
'''