from .confidence import Confidence
from .strategy import *
from indicators import *
from checks import *
from cmErrors import *
from objects.stock import *
from objects.action import *

STOP_LIMIT_MARGIN = 0.9


class HardStrategy(Strategy):

    def __init__(self, symbol, jsonStrat):
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

        self.emaFast = EMA(period=int(getVar('ema', 'fast')))
        self.emaSlow = EMA(period=int(getVar('ema', 'slow')))
        self.emaLong = EMA(period=int(getVar('ema', 'long')))

        self.macd = MACD(fastPeriod=int(getVar('macd', 'fast')),
                         slowPeriod=int(getVar('macd', 'slow')),
                         sigPeriod=int(getVar('macd', 'signal')))

        self.stoch = Stochastic(kPeriod=int(getVar('stoch', 'p')),
                                dPeriod=int(getVar('stoch', 'fast')),
                                slowPeriod=int(getVar('stoch', 'slow')))

        self.parabSAR = ParabolicSAR(af=float(getVar('parabolic', 'af')),
                                     afMax=float(getVar('parabolic', 'afmax')))

        self.atr = AverageTrueRange(period=int(getVar('atr')))

        self.dayval = BarValue()

        self.macdX = CrossoverCheck(self.macd.macd, self.macd.signal, 'up')
        self.macdX2 = CrossoverCheck(self.macd.macd, self.macd.signal, 'down')
        self.stochX = CrossoverCheck(self.stoch.percDFast, self.stoch.percDSlow, 'up')
        self.stochX2 = CrossoverCheck(self.stoch.percDFast, self.stoch.percDSlow, 'down')

        checks = [
            (Compare(self.emaFast.avg, self.emaSlow.avg, '>'), 0.35),
            (Compare(self.emaFast.avg, self.emaLong.avg, '>'), 0.05),
            (self.macdX, 0.075),
            (self.macdX2, -0.075),

            (MinCheck(self.macd.macd, 0), 0.05),
            (MinCheck(self.stoch.percDSlow, 50.0), 0.15),

            (self.stochX, 0.025),
            (self.stochX2, -0.025),

            (Compare(self.parabSAR.psar, self.dayval.close, '<'), 0.20)
        ]

        self.conf = Confidence(0.65, checks=checks)

        self.stopUpdatePeriod = int(getVar('days_to_update'))
        self.safteyFac = float(getVar('safety'))
        self.nextUpdateDay = None
        self.oldStopPrice = None

        iManage = IndicatorManager([
            self.emaSlow, self.emaLong, self.emaFast, self.macd, self.stoch, self.parabSAR,
            self.atr, self.dayval
        ])

        super(HardStrategy, self).__init__(symbol, jsonStrat['name'], iManage)

    def getNewStop(self):
        return round(self.dayval.close() - (self.atr.atr() * self.safteyFac), 2)

    def dryRun(self) -> None:
        self.conf.update()

    def nextAction(self, day: int, stock: Stock) -> Action:

        self.conf.update()

        conf, checks = self.conf.confidence()

        out = Action(stock, ActionEnum.Hold)

        pos = stock.status()

        if pos == StockStatus.OutMarket:
            if conf > 0.65:
                self.nextUpdateDay = day + self.stopUpdatePeriod
                stock.setNextStopDate(self.stopUpdatePeriod)
                stopPrice = self.getNewStop()
                self.oldStopPrice = stopPrice

                # TODO ask John about this calc
                limitPrice = round(stopPrice * STOP_LIMIT_MARGIN, 2)

                out = Action(stock, ActionEnum.Buy,
                             stopPrice=stopPrice,
                             limitPrice=limitPrice
                             )

        elif pos == StockStatus.InMarket:
            if conf < 0.45:
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
                        limitPrice = round(stopPrice * STOP_LIMIT_MARGIN, 2)

                        out = Action(stock, ActionEnum.UpdateStop,
                                     stopPrice=stopPrice,
                                     limitPrice=limitPrice
                                     )
                        self.oldStopPrice = stopPrice

        # print(f'Position: {pos.name}, Confidence: {conf:.2f}, {out}')
        return out
