from typing import Dict, Optional
from datetime import datetime

from utils.run_utils import runTradeBroker, setupStrategies
from utils.log_utils import logInfo as _logInfo, logDbg
from strategies.strategy import Strategy
from trading.brokers.backtest_broker import BacktestBroker
from trading.cm_trader import Trader

from matplotlib.figure import Figure
import matplotlib.dates as mplDates
from matplotlib.dates import ConciseDateFormatter
import json

import numpy as np

STATS = [
    ('EndValue', 'End Value $:'),
    ('Profit', 'Profit $:'),
    ('PercentGain', 'Percent Gain:'),
    ('SQN', 'SQN:'),
    ('trades', 'Num Trades:'),
    ('wins', 'Num Wins:'),
    ('losses', 'Num Losses:'),
    ('wl', 'W/L:'),
    ('winPerc', 'Win %:'),
    ('avgGain', 'Avg Gain:'),
    ('avgLoss', 'Avg Loss:'),
]

_MODULE = "Backtest"


def logInfo(m) -> None:
    _logInfo(_MODULE, m)


def logPlot(m):
    logDbg("Plot", m)


def backtest(stratName: str, strats: Dict[str, Strategy],
             masterFigure: Optional[Figure], symFigs: Optional[Dict[str, Figure]],
             startDate: datetime, endDate: datetime,
             startingVal=10000, outputFile: str = 'stats.json',
             logStatsToConsole: bool = False
             ):
    logInfo("Setting up strategies")
    bars, startIdx = setupStrategies(strats, startDate, endDate)

    logInfo("Initializing Broker")
    broker = BacktestBroker(startingVal, list(strats.keys()), bars, startIdx)
    logInfo("Initializing Trader")
    trader = Trader(strats, broker)

    logInfo("Running Backtest")
    runTradeBroker(trader, broker)

    logInfo("Calculating Stats")
    # TODO param
    runStats = broker.getRunStats(True)
    runStats["Strat"] = stratName

    logInfo("Writing stat file")
    with open(outputFile, mode='a') as f:
        json.dump(runStats, f)
        f.write('\n')

    logInfo("Plotting")
    if masterFigure is not None:
        dates = []
        for sym in bars:
            dates = [b.date for b in bars[sym][startIdx:]]
            break

        masterAxes = masterFigure.add_subplot()
        # r = range(len(portfolio_cash))

        portfolio_total = np.add(broker.portfolio_cash, broker.portfolio_value)

        logPlot("Dates vs Portfolio_cash")
        masterAxes.bar(dates, broker.portfolio_cash, label='Cash', color='C1', width=1, align='edge')
        logPlot("Dates vs Portfolio_total")
        masterAxes.plot(dates, portfolio_total, label='Value')

        locator = mplDates.AutoDateLocator(minticks=5, maxticks=10)
        dateformat = ConciseDateFormatter(locator)
        masterAxes.xaxis.set_major_locator(locator)
        masterAxes.xaxis.set_major_formatter(dateformat)

        masterAxes.grid(True)
        masterAxes.legend()

        for sym in strats.keys():
            axes = symFigs[sym].subplot_mosaic([['top'],
                                                ['bot'],
                                                ['bot']], sharex=True)

            topPlot = axes['top']
            botPlot = axes['bot']

            dates = [x.date for x in bars[sym][startIdx:]]
            closes = [x.close for x in bars[sym][startIdx:]]

            logPlot(f"{sym}: Dates vs Closes")
            botPlot.plot(dates, closes, label=sym, color=(0, 0, 0))

            stat = broker.stats[sym]

            logPlot(f"{sym}: Buy prices")
            botPlot.scatter(stat.buyDays, stat.buyPrices, marker='^', color=(0.1, 0.75, 0.1), label='Buys', zorder=2.5)
            logPlot(f"{sym}: Sell prices")
            botPlot.scatter(stat.sellDays, stat.sellPrices, marker='v', color=(1, 0.1, 0.1), label='Sells', zorder=2.5)

            botPlot.xaxis.set_major_locator(locator)
            botPlot.xaxis.set_major_formatter(dateformat)

            botPlot.legend()
            botPlot.grid(True)

            color = ['g' if x > 0 else 'r' for x in stat.sellDeltas]

            logPlot(f"{sym}: Sell deltas")
            topPlot.scatter(stat.sellDays, stat.sellDeltas, color=color, label='Profit/Loss')
            topPlot.set_yticks([0])
            topPlot.grid(True)

            topPlot.legend()

        return runStats


if __name__ == "__main__":
    from argparse import ArgumentParser
    from strategies.customStrategy import makeCustomStrategy
    from utils.file_utils import loadStratFile
    from utils.run_utils import loadSystem

    loadSystem()


    def _main():
        parser = ArgumentParser()

        parser.add_argument(
            '--strategy', '-str',
            required=True,
            type=str
        )

        args = parser.parse_args()

        strat = loadStratFile(args.strategy)
        start_date = datetime(2018, 1, 1)
        end_date = datetime.today()

        strats = {
            'QQQ': makeCustomStrategy(strat, 'QQQ'),
            'DIA': makeCustomStrategy(strat, 'DIA'),
        }

        backtest('TEST', strats=strats, masterFigure=None, symFigs=None,
                 startDate=start_date, endDate=end_date)


    _main()
