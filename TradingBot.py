from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import json
import websocket
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# TEST COMMENT FOR ACCOUNT CHANGE


# Constants for scalping strategy
stock_symbol = 'BTCUSD'
short_ema_period = 5
long_ema_period = 20
rsi_period = 14
rsi_overbought = 70
rsi_oversold = 30

# Alpaca account
trading_client = TradingClient(os.getenv('PAPER_API'), os.getenv('PAPER_SECRET'), paper=True)

# Current trade state
in_trade = False
buy_price = 0
buy_amount = 100
historical_prices = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close'])

# Set up logging
logging.basicConfig(level=logging.INFO)

# Function to calculate EMA
def calculate_ema(prices, period):
    return round(prices.ewm(span=period, adjust=False).mean().iloc[-1],1)

# Function to calculate RSI
def calculate_rsi(prices, period):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

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

# Trading bot logic
def trading_bot(new_data):
    global in_trade, buy_price, buy_amount, current_price, historical_prices
    current_price = new_data['close']
    
    # Update historical prices with new data
    new_row = pd.DataFrame([new_data])
    historical_prices = pd.concat([historical_prices, new_row], ignore_index=True)
    
    short_ema = None
    long_ema = None
    rsi = None
    if len(historical_prices) > long_ema_period:
        # Calculate indicators
        historical_prices = historical_prices.iloc[1:]
        short_ema = calculate_ema(historical_prices['close'], short_ema_period)
        long_ema = calculate_ema(historical_prices['close'], long_ema_period)
        rsi = calculate_rsi(historical_prices['close'], rsi_period)
        
        # Check for entry conditions
        if short_ema > long_ema and rsi < rsi_overbought and not in_trade:
            print("Buying")
            place_buy_order()
        
        # Check for exit conditions
        elif short_ema < long_ema or rsi > rsi_overbought and in_trade:
            print("Selling")
            place_sell_order()

    print(f"""
New Data: {new_data}
Current Price: {current_price}
Short EMA: {short_ema}
Long EMA: {long_ema}
RSI: {rsi}
Historical Price Length: {len(historical_prices)}
""")

# WebSocket functions
def on_message(ws, message):
    data = json.loads(message)
    kline = data['data']['k']
    new_data = {
        'timestamp': kline['t'],
        'open': round(float(kline['o']),1),
        'high': round(float(kline['h']),1),
        'low': round(float(kline['l']),1),
        'close': round(float(kline['c']),1)
    }
    trading_bot(new_data)

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