import threading
import time
import asyncio

from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce

import cash_money.utils.api_utils as api_utils


def close_all(api: api_utils.CMAPI):
    print("Closing all positions")
    api.trade.close_all_positions(True)


async def tradeHandler(data):
    print(type(data))


def main():
    print("Load api")
    api = api_utils.loadPaperAPI()

    print("subscribe")
    api.trade_stream.subscribe_trade_updates(tradeHandler)

    print("start thread")
    threading.Thread(target=api.trade_stream.run).start()

    print("submit order")
    api.trade.submit_order(
        MarketOrderRequest(
            symbol="QQQ",
            qty=10,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.SIMPLE
        )
    )

    print("sleep")
    time.sleep(10)

    print("close websocket")
    asyncio.run(api.trade_stream.stop_ws())


if __name__ == "__main__":
    main()
