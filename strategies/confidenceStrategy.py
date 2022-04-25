from typing import List, Tuple

from checks.check import CheckParent
from checks import *

from objects.stock import Stock
from objects.action import Action
from checks.confidence import Confidence
from checks.checkManager import CheckManager
from strategies.customStrategy import CustomStrategy, StopCalculation
from indicators.indicatorManager import IndicatorManager
from indicators import *


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

    for i in stratvars['indicators']:
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
        iManage=IndicatorManager(all_inds),
        entryChecks=entryChecks, enterMinConf=stratvars['enterConf'],
        exitChecks=exitChecks, exitMinConf=stratvars['exitConf'],
        stopCalc=stopCalc,
        stopUpdatePeriod=stratvars['stop']['daysToUpdateStop']
    )