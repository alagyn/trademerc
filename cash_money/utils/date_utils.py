# date utilities
from datetime import timedelta, datetime


def isBusinessDay(a: datetime):
    return 0 <= a.weekday() <= 4


def calcSetupStartDate(endDay: datetime, setupTime):
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


def nextBusinessDay(a: datetime):
    out = a + timedelta(1)
    while not isBusinessDay(out):
        out += timedelta(1)

    return out


def deltaBusinessDays(a: datetime, b: datetime) -> int:
    if a == b:
        return 0

    if a < b:
        cur = a
        last = b
    else:
        cur = b
        last = a

    businessDays = 0

    while cur != last:
        new = cur + timedelta(1)
        if isBusinessDay(new):
            businessDays += 1
        cur = new

    return businessDays