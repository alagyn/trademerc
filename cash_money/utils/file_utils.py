import json
from typing import List


def loadStockFile(file: str) -> List[str]:
    stocks = set()
    with open(file, mode='r') as f:
        lines = [x.strip() for x in f.readlines()]
        for x in lines:
            if len(x) > 0 and not x.startswith('#'):
                stocks.add(x)

    return list(sorted(stocks))


def loadStratFile(file: str):
    with open(file, mode='r') as f:
        strat = json.load(f)
        return strat
