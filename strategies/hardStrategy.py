from .strategy import *
from indicators import *
from checks import *
from cmErrors import *
from objects.stock import *
from objects.action import *

STOP_LIMIT_MARGIN = 0.9

stats = {
    'emafast': [],
    'emaslow': [],
    'emalong': [],
    'dates': [],
    'closes': [],
    'macd': [],
    'macdSig': [],
    'psar': [],
    'stochK': [],
    'stochDF': [],
    'stochDS': [],
    'co1U': [],
    'co1D': [],
    'co2U': [],
    'co2D': [],
    'conf': [],
    'checks': []
}


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
            (CompareGreaterThan(self.emaFast.avg, self.emaSlow.avg), 0.35),
            (CompareGreaterThan(self.emaFast.avg, self.emaLong.avg), 0.05),
            (self.macdX, 0.075),
            (self.macdX2, -0.075),

            (MinCheck(self.macd.macd, 0), 0.05),
            (MinCheck(self.stoch.percDSlow, 50.0), 0.15),

            (self.stochX, 0.025),
            (self.stochX2, -0.025),

            (CompareLessThan(self.parabSAR.psar, self.dayval.close), 0.20)
        ]

        self.conf = ConfidenceCheck(0.65, checks=checks)

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

        stats['emafast'].append(round(self.emaFast.avg(), 2))
        stats['emaslow'].append(round(self.emaSlow.avg(), 2))
        stats['emalong'].append(round(self.emaLong.avg(), 2))
        stats['closes'].append(round(self.dayval.close(), 2))
        stats['macd'].append(round(self.macd.macd(), 2))
        stats['macdSig'].append(round(self.macd.signal(), 2))
        stats['psar'].append(round(self.parabSAR.psar(), 2))
        stats['stochK'].append(round(self.stoch.percK(), 2))
        stats['stochDF'].append(round(self.stoch.percDFast(), 2))
        stats['stochDS'].append(round(self.stoch.percDSlow(), 2))
        stats['co1U'].append(bool(self.macdX.check()))
        stats['co1D'].append(bool(self.macdX2.check()))
        stats['co2U'].append(bool(self.stochX.check()))
        stats['co2D'].append(bool(self.stochX2.check()))


        conf, checks = self.conf.confidence()

        stats['checks'].append(checks)

        stats['conf'].append(conf)

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
