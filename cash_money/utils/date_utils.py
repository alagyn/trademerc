# datetime utilities
from typing import Union
from datetime import datetime, timedelta, date


def isBusinessDay(a: date):
    return 0 <= a.weekday() <= 4


def calcSetupStartDate(endDay: date, setupTime):
    out = endDay
    # find the first business day
    while not isBusinessDay(out):
        out -= timedelta(1)

    # go back setupTime business days
    while setupTime >= 0:
        out -= timedelta(1)
        if isBusinessDay(out):
            setupTime -= 1

    return out


def nextBusinessDay(a):
    out = a + timedelta(1)
    while not isBusinessDay(out):
        out += timedelta(1)

    return out


def deltaBusinessDays(a: datetime, b: datetime) -> int:
    if a.date() == b.date():
        return 0

    if a.date() < b.date():
        cur = a.date()
        last = b.date()
    else:
        cur = b.date()
        last = a.date()

    businessDays = 0

    while cur != last:
        new = cur + timedelta(1)
        if isBusinessDay(new):
            businessDays += 1
        cur = new

    return businessDays