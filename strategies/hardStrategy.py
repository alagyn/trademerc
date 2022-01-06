from .strategy import *
from indicators import *
from checks import *
from cmErrors import *
from objects.stock import *
from objects.action import *

STOP_LIMIT_MARGIN = 0.9


class HardStrategy(Strategy):

    def __init__(self, symbol, jsonStrat):
        super(HardStrategy, self).__init__(symbol, jsonStrat['name'])

        def getVar(*path):
            cur = jsonStrat['variables']
            try:
                for x in path:
                    cur = cur[x]
                return cur
            except KeyError:
                p = ''
                for idx, x in enumerate(path):
                    p += x
                    if idx + 1 < len(path):
                        p += '->'

                raise StrategyError(f'Missing Strategy Variable: {p}')

        self.emaFast = EMA(period=int(getVar('ema', 'fast'))).set(self.symbol)
        self.emaSlow = EMA(period=int(getVar('ema', 'slow'))).set(self.symbol)
        self.emaLong = EMA(period=int(getVar('ema', 'long'))).set(self.symbol)

        self.macd = MACD(fastPeriod=int(getVar('macd', 'fast')),
                         slowPeriod=int(getVar('macd', 'slow')),
                         sigPeriod=int(getVar('macd', 'signal'))).set(self.symbol)

        self.stoch = Stochastic(kPeriod=int(getVar('stoch', 'p')),
                                dPeriod=int(getVar('stoch', 'fast')),
                                slowPeriod=int(getVar('stoch', 'slow'))).set(self.symbol)

        self.parabSAR = ParabolicSAR(af=float(getVar('parabolic', 'af')),
                                     afMax=float(getVar('parabolic', 'afmax'))).set(self.symbol)

        self.atr = AverageTrueRange(period=int(getVar('atr'))).set(self.symbol)

        self.dayval = BarValue().set(self.symbol)

        self.macdX = CrossoverCheck(self.macd.macd, self.macd.signal, 'up')
        self.stochX = CrossoverCheck(self.stoch.percK, self.stoch.percD, 'up')

        checks = [
            (self.macdX, 0.15),
            (self.stochX, 0.05),
            (CompareGreaterThan(self.emaFast.avg, self.emaSlow.avg), 0.35),
            (CompareGreaterThan(self.emaFast.avg, self.emaLong.avg), 0.05),
            (MinCheck(self.macd.signal, 0), 0.05),
            (MinCheck(self.stoch.percD, 50.0), 0.15),
            (CompareLessThan(self.parabSAR.psar, self.dayval.close), 0.20)
        ]

        self.conf = ConfidenceCheck(0.5, checks=checks)

        self.stopUpdatePeriod = int(getVar('days_to_update'))
        self.safteyFac = float(getVar('safety'))
        self.nextUpdateDay = None
        self.oldStopPrice = None

    def getNewStop(self):
        return self.dayval.close() - (self.atr.atr() * self.safteyFac)

    def nextAction(self, day: int, stock: Stock) -> Action:

        conf = self.conf.check()
        out = Action(stock, ActionEnum.Hold)

        pos = stock.status()

        if pos == StockStatus.OutMarket:
            if conf:
                self.nextUpdateDay = day + self.stopUpdatePeriod
                stock.setNextStopDate(self.stopUpdatePeriod)
                stopPrice = self.getNewStop()
                self.oldStopPrice = stopPrice

                # TODO ask John about this calc
                limitPrice = stopPrice * STOP_LIMIT_MARGIN

                out = Action(stock, ActionEnum.Buy,
                             stopPrice=stopPrice,
                             limitPrice=limitPrice
                             )

        elif pos == StockStatus.InMarket:
            if not conf:
                self.nextUpdateDay = None
                self.oldStopPrice = None

                out = Action(stock, ActionEnum.Sell)
            elif self.nextUpdateDay is not None:
                if day >= self.nextUpdateDay:
                    self.nextUpdateDay = day + self.stopUpdatePeriod
                    stock.setNextStopDate(self.stopUpdatePeriod)
                    stopPrice = self.getNewStop()

                    if stopPrice > self.oldStopPrice:
                        # TODO ask John about this calc
                        limitPrice = stopPrice * 0.95

                        out = Action(stock, ActionEnum.UpdateStop,
                                     stopPrice=stopPrice,
                                     limitPrice=limitPrice
                                     )
                        self.oldStopPrice = stopPrice

        # print(f'Position: {pos.name}, Confidence: {conf:.2f}, {out}')
        return out
