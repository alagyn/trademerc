import datetime
import sys
from argparse import ArgumentParser
from typing import List

from cash_money.trading.cm_trader import Trader
from cash_money.trading.nodeStrategy import NodeStrategy
from cash_money.trading.notifiers.emailer import CMEmailer
from cash_money.trading.brokers.alpaca_broker import AlpacaBroker, SecTF, DailyTF
from cash_money.utils.file_utils import loadStockFile, loadStratFile
from cash_money.utils.run_utils import runTradeBroker, loadSystem, setupStrategies
from cash_money.utils.log_utils import CMLogger
from cash_money.utils.api_utils import loadLiveAPI, loadPaperAPI


log = CMLogger("Run Alpaca")


def runTrader(*, stratFile: str = None, stockFile: str = None, liveRun: bool = False,
              stocks: List[str] = None, stratVars=None):
    config = loadSystem()
    apiCfg = config['Alpaca']

    if stratFile is not None:
        log.logInfo('Loading Strategy')
        stratVars = loadStratFile(stratFile)

    if stockFile is not None:
        log.logInfo('Loading Stocks')
        stocks = loadStockFile(stockFile)

    strats = {}
    for sym in stocks:
        strats[sym] = NodeStrategy(stratVars)

    log.logInfo('Setting up strategies')
    setupStrategies(strats, datetime.datetime.now())

    if config['System'].getboolean('EnableNotify'):
        emailer = CMEmailer(config['Email'])
    else:
        emailer = None

    if liveRun:
        x = input('Are you sure you want to run using the LIVE ACCOUNT? (YES/NO):')
        if x != 'YES':
            sys.exit()
        else:
            api = loadLiveAPI(apiCfg)

    else:
        api = loadPaperAPI(apiCfg)

    tfType = apiCfg['Timeframe']

    if tfType == "second":
        tf = SecTF(api, float(apiCfg['Timeframe_value']))
    elif tfType == "daily":
        anchor, offset = apiCfg['Timeframe_value'].strip().split(" ")
        tf = DailyTF(api, anchor, float(offset))
    else:
        raise RuntimeError("Invalid Timeframe type")

    broker = AlpacaBroker(api, stocks, emailer, tf)
    trader = Trader(strats, broker)

    try:
        runTradeBroker(trader, broker)
    except KeyboardInterrupt:
        broker.postRun()


if __name__ == '__main__':
    def main():
        parser = ArgumentParser()

        parser.add_argument('-s', '--strat', required=True)
        parser.add_argument('-stx', '--stocks', required=True)
        parser.add_argument('--liveRun', action='store_true')
        # parser.add_argument('-c', '--cashOnly', action='store_true')

        args = parser.parse_args()
        runTrader(stratFile=args.strat, stockFile=args.stocks, liveRun=args.liveRun)


    main()
