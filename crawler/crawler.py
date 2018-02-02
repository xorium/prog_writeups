#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Requirements:
sudo pip3 install ws4py
"""

import os
import sys
import json
import time
import traceback
import logging

from datetime import datetime
from threading import Thread
from ws4py.client.threadedclient import WebSocketClient


"""
WebsocketWorker class is for receiving, handling and saving
data into global information varible
"""
class WebsocketWorker(WebSocketClient):
    def __init__(self, *args, **kwargs):
        self.symbol = kwargs.pop("symbol", None)

        super().__init__(*args, **kwargs)

        if not self.symbol:
            logger.error("[-] Error: symbol is empty!")
            sys.exit(1)

        self.book = {}
        self.ticker = {}

        self._book_chnl = 0
        self._ticker_chnl = 0

        #restoring data from global variable (if thread has been
        #crashed with exception)
        if self.symbol in all_info:
            self.book = all_info[self.symbol]['book']
            self.ticker = all_info[self.symbol]['ticker']


    def send_request(self, data):
        #unicode type is not defined in python3
        if not isinstance(data, str):
            data = json.dumps(data, default=str)
        self.send(data)

    def subscribe_for_books(self):
        subscribe_obj = {
            "event": "subscribe",
            "channel": "book",
            "prec": "R0",
            "symbol": self.symbol,
            "len": 25
        }
        self.send_request(subscribe_obj)

    def subscribe_for_tickers(self):
        subscribe_obj = { 
            "event": "subscribe", 
            "channel": "ticker", 
            "symbol": self.symbol
        }
        self.send_request(subscribe_obj)

    def opened(self):
        logger.info("Connection opened!")
        self.subscribe_for_books()
        self.subscribe_for_tickers()

    def closed(self, code, reason=None):
        logger.info("Connection closed with code: {}, reason: {}".format(code, reason))

    def is_data_msg(self, msg):
        if msg[1] == "hb":
            return False
        return True

    #event handling method (when subscribing to channels):
    #saving metadata into class variables
    def handle_event(self, msg):
        if msg["event"] == "subscribed":
            if msg["channel"] == "book":
                self._book_chnl = msg["chanId"]
            elif msg["channel"] == "ticker":
                self._ticker_chnl = msg["chanId"]
        elif msg["event"] == "error":
            logger.error("Error for channel {}, symbol: {}, text: {}"
                .format(msg['channel'], self.symbol, msg['msg']))
            self.close()

    #handling book message receiving: adding or updating
    #orders information
    def handle_book(self, msg):
        info = {
            "order_id": msg[1],
            "price": msg[2],
            "amount": msg[3]
        }
        
        if info['price'] > 0: logger.debug("book msg: {}".format(info))
        
        if info["price"] > 0:
            self.book[info["order_id"]] = info
        elif info["price"] == 0:
            self.book.pop(info["order_id"], None)

    #handling ticker message: updating price info
    def handle_ticker(self, msg):
        info = {
            "latest_price": msg[9]
        }
        
        self.ticker.update(info)
    
    #method implements messages handling logic
    def received_message(self, msg):
        global all_info

        #parsing message (string in JSON format)
        try:
            msg = json.loads(msg.data.decode("utf-8"))
        except Exception:
            logger.error("[-] Error: can't parse message: {}".format(msg))
            return

        if "event" in msg:
            self.handle_event(msg)
            return

        if not self.is_data_msg(msg):
            return

        #handling each type of message recieved
        if msg[0] == self._book_chnl:
            self.handle_book(msg)
        elif msg[0] == self._ticker_chnl:
            self.handle_ticker(msg)

        #updating info in all_info global variable
        all_info[self.symbol] = {
            "book": self.book,
            "ticker": self.ticker
        }

"""
WorkerThread class is for managing: creating and restarting websocket
connections
"""
class WorkerThread(Thread):
    def __init__(self, symbol, api_url="wss://api.bitfinex.com/ws/"): 
        super().__init__()
        self.symbol = symbol
        self.api_url = api_url
 
    def run(self):
        while True:
            ws = WebsocketWorker(self.api_url, symbol=self.symbol)
            try:
                logger.info("Starting worker for {}".format(self.symbol))
                ws.connect()
                ws.run_forever()
                ws.close()
            except Exception:
                if DBG:
                    logger.error("[!] Error: \n{}".format(traceback.format_exc()))
            #sleeping before restarting
            time.sleep(3)

#converting data to more readble structure
def prepare_data():
    result = {}

    for symbol, info in all_info.items():
        tmp = {}
        tmp['latest_price'] = info['ticker'].get("latest_price", None)
        tmp['order_book'] = [order for order in info['book'].values()]
        tmp['timestamp'] = str(datetime.now())

        #skipping empty values
        if not tmp['latest_price'] and not len(tmp['order_book']):
            continue

        result[symbol] = tmp

    return result

"""
Saving info to the output file.
Format: JSON strings, separated by '\n' symbol (in *nix)
Every JSON object has the following format:
{
    "timestamp": "2018-01-30 23:03:12.556811", //item timestamp
    "latest_price": 169.5,                     //latest price
    "order_book": [                            //order book
        {
            "amount": -7.49,                   //order amount
            "order_id": 123,                   //order ID in bitfinex.com
            "price": 170.74                    //order price
        },
        ...
    ]
}
"""
def save_info():
    if DBG:
        logger.debug("all_info: {}".format(all_info))

    data = prepare_data()
    if not len(data.keys()):
        logger.debug("Data is empty, skipping writing..")
        return
    
    for symbol, value in data.items():
        fname = "{}.txt".format(symbol.lower())
        with open(fname, "a+") as f:
           json_data = json.dumps(value, default=str) + os.linesep
           f.write(json_data)

#main function: starts all threads
def main():
    threads = []

    #initializing threads
    for symb in symbols:
        t = WorkerThread(symbol=symb)
        threads.append(t)
        t.start()

    #save information in loop
    while True:
        try:
            save_info()
            time.sleep(delay)
        except KeyboardInterrupt:
            break

    for t in threads:
        t.join()

#configuring script logging
def init_logging():
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.basicConfig(filename='crawler.log', level=logging.DEBUG)
    log_level = logging.DEBUG

    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    
    return logger

if __name__ == "__main__":
    logger = init_logging()

    DBG = True

    all_info = {} #global variable for all information
    delay = 1 #timeout for saving info process (in seconds)
    symbols = ["tBTCUSD", "tLTCUSD", "tETHUSD", "tXRPUSD", "tNEOUSD"] #symbols for monitoring

    main()