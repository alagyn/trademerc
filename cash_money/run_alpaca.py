import datetime
import sys
from argparse import ArgumentParser
from typing import List, Optional
import logging

from cash_money.trading.nodeStrategy import NodeStrategy, loadStratFromJson
from cash_money.trading.notifiers.push_bullet_notifier import PushBulletNotifier
from cash_money.trading.notifiers.email_notifier import EmailNotifier
from cash_money.trading.notifiers.console_notifier import ConsoleNotifier
from cash_money.trading.brokers.alpaca_trader import AlpacaTrader
from cash_money.trading.brokers.timeframes.dailyTF import DailyTF
from cash_money.trading.brokers.timeframes.secondTF import SecTF
from cash_money.utils.file_utils import loadStockFile, loadStratFile
from cash_money.utils.run_utils import runTrader, loadSystem, setupStrategies, loadDataBroker
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

    if stratVars is None:
        raise RuntimeError()

    strats = {}
    for sym in stocks:
        strats[sym] = loadStratFromJson(stratVars, sym)

    databroker = loadDataBroker(config)

    log.info('Setting up strategies')
    setupStrategies(strats, datetime.datetime.today(), databroker)

    if liveRun:
        log.warning("Loading Live API")
        api = loadLiveAPI(apiCfg)
    else:
        log.warning("Loading Paper API")
        api = loadPaperAPI(apiCfg)

    tfType = apiCfg['Timeframe']

    if tfType == "second":
        tf = SecTF(api, float(apiCfg['Timeframe_value']))
    elif tfType == "daily":
        anchor, offset = apiCfg['Timeframe_value'].strip().split(" ")
        tf = DailyTF(api, anchor, float(offset))
    else:
        raise RuntimeError("Invalid Timeframe type")

    trader = AlpacaTrader(strats, api, tf)

    notifyType = config['System']['Notify']
    notifier = None
    # TODO error check ^^
    if notifyType == "None":
        # notifier = CMEmailer(config['Email'])
        pass
    elif notifyType == "PushBullet":
        log.info("Loading PushBullet Notifier")
        notifier = PushBulletNotifier(config)
        trader.addListener(notifier)
    elif notifyType == 'Console':
        log.info("Loading Console notifier")
        # does nothing, loaded below
    elif notifyType == 'Email':
        log.info("Loading Email notifier")
        notifier = EmailNotifier(config)
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
        if isinstance(notifier, PushBulletNotifier):
            notifier.send_message(f"Error {err}")
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
