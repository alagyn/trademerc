
from trading.cm_trader import Trader
from trading.brokers.broker import Broker

def runTradeBroker(trader: Trader, broker: Broker):
    broker.preRun()

    while True:
        broker.incDay()

        if not broker.preTrade():
            break

        trader.trade()
        broker.postTrade()

    broker.postRun()
