import datetime
import sys
from argparse import ArgumentParser
from typing import List, Optional
import logging

from cash_money.trading.nodeStrategy import NodeStrategy
from cash_money.trading.notifiers.push_bullet_notifier import PushBulletNotifier
from cash_money.trading.notifiers.console_notifier import ConsoleNotifier
from cash_money.trading.brokers.alpaca_trader import AlpacaTrader
from cash_money.trading.brokers.timeframes.dailyTF import DailyTF
from cash_money.trading.brokers.timeframes.secondTF import SecTF
from cash_money.utils.file_utils import loadStockFile, loadStratFile
from cash_money.utils.run_utils import runTrader, loadSystem, setupStrategies
from cash_money.utils.api_utils import loadLiveAPI, loadPaperAPI
from cash_money.cmErrors import CMError

log = logging.getLogger("Run Alpaca")


def runAlpacaTrader(
    *,
    stratFile: Optional[str] = None,
    stockFile: Optional[str] = None,
    liveRun: bool = False,
    stocks: Optional[List[str]] = None,
    stratVars=None
):
    config = loadSystem()
    apiCfg = config['Alpaca']

    if stratFile is not None:
        log.info('Loading Strategy')
        stratVars = loadStratFile(stratFile)['graph']

    if stocks is None:
        if stockFile is not None:
            log.info('Loading Stocks')
            stocks = loadStockFile(stockFile)
        else:
            raise CMError("run_alpaca.runTrader() No stocks or stock file provided")

    strats = {}
    for sym in stocks:
        strats[sym] = NodeStrategy(stratVars, sym)

    log.info('Setting up strategies')
    setupStrategies(strats, datetime.datetime.today())

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

    trader = AlpacaTrader(strats, api, stocks, tf)

    notifyType = config['System']['Notify']
    # TODO error check ^^
    if notifyType == "None":
        # notifier = CMEmailer(config['Email'])
        pass
    elif notifyType == "PushBullet":
        notifier = PushBulletNotifier(config)
        trader.addListener(notifier)
    else:
        raise CMError(f"run_alpaca.runTrader() Invalid notifier type \"{notifyType}\"")

    # Always add a console notifier for now
    trader.addListener(ConsoleNotifier())

    try:
        runTrader(trader)
    except KeyboardInterrupt:
        pass
    except Exception as err:
        print(err)

    finally:
        # Errors will be logged in runTradeBroker
        trader.postRun()


if __name__ == '__main__':

    def main():
        parser = ArgumentParser()

        parser.add_argument('-s', '--strat', required=True)
        parser.add_argument('-stx', '--stocks', required=True)
        parser.add_argument('--liveRun', action='store_true')
        # parser.add_argument('-c', '--cashOnly', action='store_true')

        args = parser.parse_args()
        runAlpacaTrader(stratFile=args.strat, stockFile=args.stocks, liveRun=args.liveRun)

    main()
