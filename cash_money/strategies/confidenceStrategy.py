from typing import List, Tuple

from cash_money.checks.check import CheckParent
from cash_money.checks import *

from cash_money.objects.stock import Stock
from cash_money.objects.action import Action
from cash_money.checks.confidence import Confidence
from cash_money.checks.checkManager import CheckManager
from cash_money.strategies.customStrategy import CustomStrategy, StopCalculation
from cash_money.indicators.indicatorManager import IndicatorManager
from cash_money.indicators import *
from cash_money.indicators.lineManager import LineManager


class ConfidenceStrategy(CustomStrategy):
    def __init__(self, name: str, symbol: str, iManage: IndicatorManager,
                 entryChecks: List[Tuple[CheckParent, float]], enterMinConf: float,
                 exitChecks: List[Tuple[CheckParent, float]], exitMinConf: float,
                 stopCalc: StopCalculation, stopUpdatePeriod=0
                 ):
        self.entryConf = Confidence(
            minConf=enterMinConf,
            checks=entryChecks
        )

        self.exitConf = Confidence(
            minConf=exitMinConf,
            checks=exitChecks
        )

        # only use these checks as their updates will update children
        cManage = CheckManager([self.entryConf, self.exitConf])

        super().__init__(name, symbol, iManage, cManage,
                         enterCond=self.entryConf,
                         exitCond=self.exitConf,
                         stopCalc=stopCalc,
                         stopUpdatePeriod=stopUpdatePeriod
                         )


    def nextAction(self, day: int, stock: Stock) -> Action:
        action = super().nextAction(day, stock)
        action.args['confidence'] = f'{self.entryConf.confidence():.2%}'
        return action

def makeConfidenceStrat(stratvars, symbol: str) -> ConfidenceStrategy:
    # TODO json error catching
    # TODO warn if an indicator is not used

    all_inds: List[Indicator] = []

    lineManager = LineManager()

    for i in stratvars['indicators']:
        params = i['params']
        params['name'] = i['name']
        params['lineManager'] = lineManager
        newind = INDICATORS[i['classname']](**i['params'])
        all_inds.append(newind)

    def iterChecks(l: Dict) -> List[Tuple[CheckParent, float]]:
        out = []
        for c_idx, c in enumerate(l):
            valFuncs = []
            for _i in c['indicators']:
                idx = _i['idx']
                key = _i['key']
                valFuncs.append(all_inds[idx][key])

            newcheck = CHECKS[c['classname']].factory(valFuncs, c['params'])
            out.append((newcheck, float(c['weight'])))

        return out

    entryChecks = iterChecks(stratvars['entryChecks'])
    exitChecks = iterChecks(stratvars['exitChecks'])

    stopCalcIdx = stratvars['stop']['indicator']
    stopCalcKey = stratvars['stop']['key']

    stopCalcVal = all_inds[stopCalcIdx][stopCalcKey]
    stopScale = stratvars['stop']['scale']
    stopLimitScale = stratvars['stop']['limitScale']

    stopCalc = StopCalculation(stopCalcVal, stopScale, stopLimitScale)



    return ConfidenceStrategy(
        name=stratvars['name'],
        symbol=symbol,
        iManage=IndicatorManager(all_inds, lineManager),
        entryChecks=entryChecks, enterMinConf=stratvars['enterConf'],
        exitChecks=exitChecks, exitMinConf=stratvars['exitConf'],
        stopCalc=stopCalc,
        stopUpdatePeriod=stratvars['stop']['daysToUpdateStop']
    )