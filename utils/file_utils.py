import json
from cmErrors import *
from consts import STRAT_FORMAT


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
        verifyStrat(strat)
        return strat


def recursVerify(fmt, strat, path):
    for key, val in fmt.items():
        curPath = path + '->' + key
        try:
            stratVal = strat[key]
        except KeyError:
            raise JSONStrategyMissingVal(curPath)

        if not isinstance(stratVal, type(val)):
            if not (isinstance(val, float) and isinstance(stratVal, int)):
                raise JSONStrategyInvalidType(curPath, type(val), type(stratVal))

        if isinstance(val, dict):
            recursVerify(val, stratVal, curPath)


def verifyStrat(strat):
    with open(STRAT_FORMAT, mode='r') as f:
        fmt = json.load(f)

    # print(fmt)
    recursVerify(fmt, strat, "root")
