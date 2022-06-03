import json


def loadStockFile(file):
    stocks = []
    with open(file, mode='r') as f:
        lines = [x.strip() for x in f.readlines()]
        for x in lines:
            if len(x) > 0 and not x.startswith('#'):
                stocks.append(x)

    return stocks


def loadStratFile(file):
    with open(file, mode='r') as f:
        strat = json.load(f)
        return strat

