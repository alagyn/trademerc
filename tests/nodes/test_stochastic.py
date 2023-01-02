import unittest
from .data import RAW_TEST_DATA, DatamapIter
from cash_money.nodes.stochasticNode import Stochastic, DP, KP, SP
from collections import deque

class StochTest(unittest.TestCase):
    def test_Stoch(self):
        expected = []

        lows = deque()
        highs = deque()

        percKList = deque()
        percDList = deque()

        # TODO make const
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

        stoch = Stochastic()
        stoch.args[KP].value = 5
        stoch.args[DP].value = 10
        stoch.args[SP].value = 10
        stoch.setup()

        i = DatamapIter(stoch, RAW_TEST_DATA)

        percKOut = stoch.percKOut
        percDOut = stoch.percDOut
        percDSOut = stoch.percDSOut

        for idx, e in enumerate(expected):
            next(i)
            stoch.execute()

            self.assertAlmostEqual(e[0], percKOut.value, 2, msg=f'Idx: {idx}')
            self.assertAlmostEqual(e[1], percDOut.value, 2, msg=f'Idx: {idx}')
            self.assertAlmostEqual(e[2], percDSOut.value, 2, msg=f'Idx: {idx}')
