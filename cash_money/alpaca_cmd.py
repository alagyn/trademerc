import threading
import time
import asyncio

from alpaca.trading.requests import MarketOrderRequest, OrderRequest, StopLossRequest
from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce, OrderType

import cash_money.utils.api_utils as api_utils


def close_all(api: api_utils.CMAPI):
    print("Closing all positions")
    api.trade.close_all_positions(True)


async def tradeHandler(data):
    print(type(data))
    print(data)


def main():
    print("Load api")
    api = api_utils.loadPaperAPI()
    api.trade.close_all_positions(True)


if __name__ == "__main__":
    main()
