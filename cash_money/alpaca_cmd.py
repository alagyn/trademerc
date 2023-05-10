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

    print("subscribe")
    api.trade_stream.subscribe_trade_updates(tradeHandler)

    print("start thread")
    threading.Thread(target=api.trade_stream.run).start()

    print("submit order")
    order = api.trade.submit_order(
        OrderRequest(
            symbol="QQQ",
            qty=10,
            notional=None,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.OTO,
            extended_hours=False,
            client_order_id=None,
            take_profit=None,
            stop_loss=StopLossRequest(stop_price="323.15") # type: ignore
        )
    )

    print("sleep")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print(order)

    print("close websocket")
    asyncio.run(api.trade_stream.stop_ws())


if __name__ == "__main__":
    main()
