from strategies.customStrategy import CustomStrategy
from strategies.confidenceStrategy import makeConfidenceStrat
from cmErrors import StrategyError

def makeCustomStrategy(stratvars, symbol: str) -> CustomStrategy:
    t = stratvars['type'].lower()
    if t == 'confidence':
        return makeConfidenceStrat(stratvars, symbol)

    raise StrategyError(f'Invalid strategy file: Unkown strat type: "{t}"')