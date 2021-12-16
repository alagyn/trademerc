from cmBroker import WeightedStrategy



class Controller:
    def __init__(self):
        self.strats = {}

    def addStrat(self, symbol, strat) -> None:
        if symbol in self.strats:
            print('Duplicate Symbol, replacing Strategy')
        self.strats[symbol] = strat



