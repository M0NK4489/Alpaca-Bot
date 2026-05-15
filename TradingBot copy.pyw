from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
import json
import websocket
from re import sub
import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Constants
stock_symbol = 'BTCUSD'  # Note: Alpaca uses BTCUSD format without '/'
resistance_level_1 = 71000
resistance_level_2 = 66500
support_level = 62000

# Alpaca account
trading_client = TradingClient(os.getenv('PAPER_API'), os.getenv('PAPER_SECRET'), paper=True)

# Current trade state
in_trade = False
buy_price = 0
buy_amount = 100  # Example amount to trade

# Function to place a buy order
def place_buy_order():
    global in_trade, buy_price
    buy_request = MarketOrderRequest(
        symbol=stock_symbol,
        notional=buy_amount,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.IOC
    )
    market_order_submission = trading_client.submit_order(order_data=buy_request)
    buy_price = current_price
    in_trade = True
    print(f"Entering trade at price: {buy_price}")

# Function to place a sell order
def place_sell_order():
    global in_trade, buy_price
    positions = trading_client.get_all_positions()
    for position in positions:
        if position.symbol == stock_symbol:
            sell_quantity = float(position.qty)
            if sell_quantity > 0:
                sell_request = MarketOrderRequest(
                    symbol=stock_symbol,
                    qty=sell_quantity,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.IOC
                )
                market_order_submission = trading_client.submit_order(order_data=sell_request)
                sell_price = current_price
                profit = sell_price - buy_price
                in_trade = False
                print(f"Exiting trade at price: {sell_price}, Profit: {profit}")
            break

# WebSocket functions
def on_message(ws, message):
    global in_trade, current_price
    data = json.loads(message)
    current_price = float(data['data']['k']['c'])

    # Check for entry conditions
    if current_price > resistance_level_1 and not in_trade:
        place_buy_order()
    
    # Check for exit conditions
    elif (current_price < support_level or current_price > resistance_level_2) and in_trade:
        place_sell_order()

def on_open(ws):
    print('''
    
                                         YOU HAVE CONNECTED TO JORDAN BELFORT
                                                  ____          ____
                                                 |oooo|        |oooo|
                                                 |oooo| .----. |oooo|
                                                 |Oooo|/\_||_/\|oooO|
                                                 `----' / __ \ `----'
                                                 ,/ |#|/\/__\/\|#| \,
                                                /  \|#|| |/\| ||#|/  \ 
                                               / \_/|_|| |/\| ||_|\_/ \ 
                                              |_\/    o\=----=/o    \/_|
                                              <_>      |=\__/=|      <_>
                                              <_>      |------|      <_>
                                              | |   ___|======|___   | |
                                             //\\\  / |O|======|O| \  //\\\ 
                                             |  |  | |O+------+O| |  |  |
                                             |\/|  \_+/        \+_/  |\/|
                                             \__/  _|||        |||_  \__/
                                                   | ||        || |
                                                  [==|]        [|==]
                                                  [===]        [===]
                                                   >_<          >_<
                                                  || ||        || ||
                                                  || ||        || ||
                                                  || ||        || ||
                                                __|\_/|__    __|\_/|__
                                               /___n_n___\  /___n_n___\ 

''')
    
    
def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws):
    print("Later Bitch")


if __name__ == "__main__":



    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/stream?streams=btcusdt@kline_1m", 
                                on_open=on_open , 
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()