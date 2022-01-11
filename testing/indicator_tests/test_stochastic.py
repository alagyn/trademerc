import unittest
from .data import RAW_TEST_DATA
from indicators.stochastic import Stochastic
from collections import deque


class StochTest(unittest.TestCase):
    def test_Stoch(self):
        expected = []

        lows = deque()
        highs = deque()

        percKList = deque()
        percDList = deque()

        for x in RAW_TEST_DATA:
            lows.append(x[0])
            highs.append(x[2])

            if len(lows) > 5:
                lows.popleft()
                highs.popleft()

            ll = min(lows)
            hh = max(highs)

            percK = (x[1] - ll) / (hh - ll)
            percK *= 100

            percKList.append(percK)

            if len(percKList) > 10:
                percKList.popleft()

            percDFast = sum(percKList) / len(percKList)

            percDList.append(percDFast)

            if len(percDList) > 10:
                percDList.popleft()

            percDSlow = sum(percDList) / len(percDList)

            expected.append((percK, percDFast, percDSlow))


        stoch = Stochastic(5, 10, 10)

        for idx, e in enumerate(expected):
            stoch.addData(*RAW_TEST_DATA[idx])

            self.assertAlmostEqual(e[0], stoch.percK(), 2, msg=f'Idx: {idx}')
            self.assertAlmostEqual(e[1], stoch.percDFast(), 2, msg=f'Idx: {idx}')
            self.assertAlmostEqual(e[2], stoch.percDSlow(), 2, msg=f'Idx: {idx}')
