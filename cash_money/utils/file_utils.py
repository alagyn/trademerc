import json
from typing import List
import re
import logging

# Regex for a valid stock symbol. Need to sanitize them since they are used in SQL queries
STOCK_RE = re.compile("[A-Za-z]+")


def loadStockFile(file: str) -> List[str]:
    stocks = set()
    with open(file, mode='r') as f:
        lines = [x.strip() for x in f.readlines()]
        for x in lines:
            if len(x) > 0 and not x.startswith('#'):
                if STOCK_RE.fullmatch(x):
                    stocks.add(x.upper())
                else:
                    logging.warning("Invalid symbol: {}, ignoring", x)

    return list(sorted(stocks))


def loadStratFile(file: str):
    with open(file, mode='r') as f:
        strat = json.load(f)
        return strat
