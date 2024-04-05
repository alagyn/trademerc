import unittest
from cash_money.stats.sma import SMA
from .data import S_TEST_DATA


class SMATest(unittest.TestCase):

    def test_sma(self):
        sma = SMA(5)

        expected = [0.1, 0.15, 0.2, 0.275, 0.26, 0.34, 0.36, 0.46, 0.54, 0.7, 0.84, 0.96, 0.98, 0.96, 0.98, 1.04, 1.14]

        for e, val in zip(expected, S_TEST_DATA):
            a = sma.next(val)
            self.assertAlmostEqual(e, a, 2)
