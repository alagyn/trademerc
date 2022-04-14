from typing import Dict, Union
from datetime import datetime, timedelta

from utils.api_utils import calcSetupStartDate
from utils.run_utils import runTradeBroker
from consts import DATE_FMT
from objects.bar import Bar
from strategies.strategy import Strategy
from trading.brokers.backtest_broker import BacktestBroker
from trading.cm_trader import Trader

import yfinance as yf
from matplotlib.figure import Figure
import matplotlib.dates as mplDates
from matplotlib.dates import ConciseDateFormatter
import json
import logging as log
import numpy as np

CLOSE = 'Close'
LOW = 'Low'
HIGH = 'High'


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

def backtest(stratName: str, strats: Dict[str, Strategy],
             masterFigure: Union[Figure, None], symFigs: Union[Dict[str, Figure], None],
             startDate: datetime, endDate: datetime,
             startingVal=10000, outputFile: str = 'stats.json',
             ):
    setupTime = max([x.getSetupTime() for x in strats.values()])

    setupStart = calcSetupStartDate(startDate - timedelta(1), setupTime)

    startstr = setupStart.strftime(DATE_FMT)

    endstr = endDate.strftime(DATE_FMT)

    # load bars and setup indicators
    length = None
    allBars = {}
    dates = None
    for sym, strat in strats.items():
        b = yf.download(sym, startstr, endstr)
        lo = b[LOW]
        c = b[CLOSE]
        hi = b[HIGH]
        if length is None:
            length = len(hi)
            dates = [b[sym].index[i] for i in range(len(b[sym]))]
        allBars[sym] = [Bar(lo[x], c[x], hi[x]) for x in range(length)]


    broker = BacktestBroker(startingVal, list(strats.keys()), allBars, dates, setupTime, length)
    trader = Trader(strats, broker)

    runTradeBroker(trader, broker)

    stats = broker.getStats()
    stats["Strat"] = stratName

    with open(outputFile, mode='a') as f:
        json.dump(stats, f)
        f.write('\n')

    log.info("Plotting")
    if masterFigure is not None:
        masterAxes = masterFigure.add_subplot()
        # r = range(len(portfolio_cash))

        portfolio_total = np.add(broker.portfolio_cash, broker.portfolio_value)

        masterAxes.bar(broker.dates, broker.portfolio_cash, label='Cash', color='C1', width=1, align='edge')
        masterAxes.plot(broker.dates, portfolio_total, label='Value')

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

            closes = [x.close for x in allBars[sym]]

            botPlot.plot(broker.dates, closes, label=sym, color=(0, 0, 0))

            stat = stats[sym]

            botPlot.scatter(stat.buyDays, stat.buyPrices, marker='^', color=(0.1, 0.75, 0.1), label='Buys', zorder=2.5)
            botPlot.scatter(stat.sellDays, stat.sellPrices, marker='v', color=(1, 0.1, 0.1), label='Sells', zorder=2.5)

            botPlot.xaxis.set_major_locator(locator)
            botPlot.xaxis.set_major_formatter(dateformat)

            botPlot.legend()
            botPlot.grid(True)

            color = ['g' if x > 0 else 'r' for x in stat.sellDeltas]

            topPlot.scatter(stat.sellDays, stat.sellDeltas, color=color, label='Profit/Loss')
            topPlot.set_yticks([0])
            topPlot.grid(True)

            topPlot.legend()

        return stats

if __name__ == "__main__":
    from argparse import ArgumentParser
    from strategies.customStrategy import makeCustomStrategy
    from utils.file_utils import loadStratFile
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

        backtest('TEST', strats={'QQQ': makeCustomStrategy(strat, 'QQQ')}, masterFigure=None, symFigs=None,
                 startDate=start_date, endDate=end_date)

    _main()