import numpy as np
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from cash_money.trading.nodeStrategy import NodeStrategy
from cash_money.utils.run_utils import runTrader, setupStrategies, loadDataBroker
from cash_money.trading.data.dataBroker import DataBroker
from cash_money.trading.brokers.backtest_trader import BacktestTrader, RunStats, BacktestStats
from cash_money.trading.trader import Trader
from cash_money.utils.file_utils import loadStockFile
from cash_money.trading.events import CMEventListener

import json

log = logging.getLogger("Backtest Run")
statLog = logging.getLogger("Stats")


def _logStats(stats: BacktestStats):
    statLog.info(f'Profit: {stats.profit:,.2f}, Percent Gain: {stats.percGain:.2%}')
    statLog.info(f'Trades: {stats.trades}, Wins: {stats.wins}, Losses: {stats.losses}, W/L: {stats.wlRatio:.2f}')
    statLog.info(f'Win %: {stats.winPerc:.2%}')
    statLog.info(f'Avg Gain: ${stats.avgGain:,.2f}')
    statLog.info(f'Avg Loss: ${stats.avgLoss:,.2f}')
    statLog.info(f'Total Won: ${stats.winValue:,.2f}')
    statLog.info(f'Total Lost: ${stats.lossValue:,.2f}')
    # statLog.info(f'SQN: {stats.sqn:.3f}')


def backtest(
    strats: Dict[str, NodeStrategy],
    startDate: datetime,
    endDate: datetime,
    dataBroker: DataBroker,
    startingVal=10000,
    outputFile: str = 'stats.json',
    listener: Optional[CMEventListener] = None,
) -> RunStats:
    log.info("Setting up strategies")

    setupStrategies(strats, startDate, dataBroker)
    # TODO this is doing the same thing?
    bars = dataBroker.getBars([sym for sym in strats], startDate, endDate)

    log.info("Initializing Trader")
    broker = BacktestTrader(strats, startingVal, bars)

    if listener is not None:
        broker.addListener(listener)

    log.info("Running Backtest")
    runTrader(broker)

    log.info("Calculating Stats")
    runStats = broker.getRunStats()

    for symbol, stats in runStats.symbolStats.items():
        statLog.info(f"----- Symbol: {symbol}")
        _logStats(stats)

    statLog.info("----- TOTAL")
    statLog.info(f'Start Value: ${runStats.startValue:,.2f}, End Value: ${runStats.endValue:,.2f}')
    _logStats(runStats.totalStats)

    # TODO
    """
    log.info("Writing stat file")
    with open(outputFile, mode='a') as f:
        json.dump(runStats.toDict(), f)
        f.write('\n')
    """

    return runStats


if __name__ == "__main__":
    from argparse import ArgumentParser
    from cash_money.utils.run_utils import loadSystem

    def _main():
        parser = ArgumentParser()

        parser.add_argument('-s', '--strat', required=True)
        parser.add_argument('-stx', '--stocks', required=True)

        args = parser.parse_args()

        config = loadSystem()

        with open(args.strat, mode='r') as f:
            strat = json.load(f)

        stocks = loadStockFile(args.stocks)
        strats = {
            sym: NodeStrategy(strat['graph'], sym)
            for sym in stocks
        }

        start_date = datetime(2021, 1, 1)
        end_date = datetime(2022, 1, 1)

        dataBroker = loadDataBroker(config)

        backtest(
            strats=strats,
            startDate=start_date,
            endDate=end_date,
            dataBroker=dataBroker,
        )

    _main()
