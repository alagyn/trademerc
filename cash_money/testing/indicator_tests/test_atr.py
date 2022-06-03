import unittest
from cash_money.indicators.averageTrueRange import AverageTrueRange
from cash_money.indicators.lineManager import LineManager
from .data import TEST_DATA


class ATRTest(unittest.TestCase):
    def test_8Day(self):
        lm = LineManager()
        atr = AverageTrueRange("TEST ATR", lm, 8)

        expected = [
            (1.68, 1.68),
            (0.76, 1.565),
            (1.72, 1.584),
            (0.77, 1.48),
            (0.97, 1.42),
            (1.44, 1.42),
            (1.10, 1.38),
            (1.72, 1.42),
            (2.88, 1.61),
            (2.04, 1.66),
            (1.07, 1.59)
        ]

        i = iter(TEST_DATA)

        self.assertIsNone(atr.atr())
        self.assertIsNone(atr.tr())

        lm.update(**next(i), volume=0)
        atr.update()
        self.assertIsNone(atr.atr())
        self.assertIsNone(atr.tr())

        for x in expected:
            lm.update(**next(i), volume=0)
            atr.update()
            self.assertAlmostEqual(x[0], atr.tr(), places=2)
            self.assertAlmostEqual(x[1], atr.atr(), delta=0.005)