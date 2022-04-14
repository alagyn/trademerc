import logging as log
import os.path
import time
from argparse import ArgumentParser
from configparser import ConfigParser
from typing import List

from strategies.customStrategy import makeCustomStrategy
from trading.cm_trader import Trader
from trading.notifiers.emailer import CMEmailer
from trading.brokers.alpaca_broker import AlpacaBroker
from utils.file_utils import loadStockFile, loadStratFile
from utils.run_utils import runTradeBroker


def runTrader(*, stratFile: str = None, stockFile: str = None, liveRun: bool = False,
              stocks: List[str] = None, stratVars=None):
    config = ConfigParser()
    config.read(r'config/system.cfg')

    logname = time.strftime(r'%Y_%b_%dT%H_%M_%S')

    if not os.path.exists('logs'):
        os.mkdir('logs')

    log.basicConfig(
        filename=f'logs/{logname}.txt',
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt=r'%Y-%m-%d %H:%M:%S',
        filemode='w',
        level=log.INFO
    )

    console = log.StreamHandler()
    console.setFormatter(log.Formatter('%(message)s'))
    console.setLevel(log.INFO)
    log.getLogger("").addHandler(console)

    apiCfg = config['Alpaca']

    if stratFile is not None:
        log.info('Loading Strategy')
        stratVars = loadStratFile(stratFile)

    if stockFile is not None:
        log.info('Loading Stocks')
        stocks = loadStockFile(stockFile)

    strats = {}
    for sym in stocks:
        strats[sym] = makeCustomStrategy(stratVars, sym)

    emailer = CMEmailer(config['Email'])

    broker = AlpacaBroker(apiCfg, stocks, emailer, liveRun)
    trader = Trader(strats, broker)

    try:
        runTradeBroker(trader, broker)
    except KeyboardInterrupt:
        broker.postRun()


def main():
    parser = ArgumentParser()

    parser.add_argument('-s', '--strat', required=True)
    parser.add_argument('-stx', '--stocks', required=True)
    parser.add_argument('--liveRun', action='store_true')
    # parser.add_argument('-c', '--cashOnly', action='store_true')

    args = parser.parse_args()
    runTrader(stratFile=args.strat, stockFile=args.stocks, liveRun=args.liveRun)


if __name__ == '__main__':
    main()
