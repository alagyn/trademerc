from cmBroker import WeightedStrategy
from indicators import *
from checks import *
from indicators.indicator import addData, getSetupTime

if __name__ == '__main__':
    strat = WeightedStrategy('QQQ')

    emaFast = EMA(period=3).set('QQQ')
    emaSlow = EMA(period=20).set('QQQ')
    emaLong = EMA(period=60).set('QQQ')

    macd = MACD(fastPeriod=10, slowPeriod=20, sigPeriod=20).set('QQQ')

    macdX = Crossover(macd.getMACD, macd.getSignal).set('QQQ')

    stoch = Stochastic(kPeriod=20, dPeriod=10, slowPeriod=10).set('QQQ')

    stochX = Crossover(stoch.percK, stoch.percD).set('QQQ')

    parabSAR = ParabolicSAR(af=0.02, afMax=0.07).set('QQQ')

    atr = AverageTrueRange(period=5).set('QQQ')

    dayval = DayValue().set('QQQ')

    checks = [
        (CompareGreaterThan(emaFast.getValue, emaSlow.getValue), 0.35),
        (CompareGreaterThan(emaFast.getValue, emaLong.getValue), 0.05),
        (MinCheck(macdX.getCrossOver, 0), 0.15),
        (MinCheck(macd.getSignal, 0), 0.05),
        (MinCheck(stoch.percD, 50), 0.15),
        (MinCheck(stochX.getCrossOver, 0), 0.05),
        (CompareLessThan(parabSAR.getSAR, dayval.close), 0.20)
    ]

    for c in checks:
        strat.addCheck(c[0], c[1])

    print(f'Setup time: {getSetupTime()}')