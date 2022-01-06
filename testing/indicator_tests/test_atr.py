import unittest
from indicators.averageTrueRange import AverageTrueRange
from .data import TEST_DATA


class ATRTest(unittest.TestCase):
    def test_8Day(self):
        atr = AverageTrueRange(8)

        i = iter(TEST_DATA)

        self.assertIsNone(atr.getATR())
        self.assertIsNone(atr.getTR())

        atr.addData(**next(i))
        self.assertIsNone(atr.getATR())
        self.assertIsNone(atr.getTR())

        atr.addData(**next(i))
        self.assertAlmostEqual(1.68, atr.getTR(), 2)
        self.assertAlmostEqual(1.68, atr.getATR(), 2)

        atr.addData(**next(i))
        self.assertAlmostEqual(0.76, atr.getTR(), 2)
        self.assertAlmostEqual(1.565, atr.getATR(), 3)

        atr.addData(**next(i))
        self.assertAlmostEqual(1.72, atr.getTR(), 2)
        self.assertAlmostEqual(1.584, atr.getATR(), 3)

        atr.addData(**next(i))
        self.assertAlmostEqual(0.77, atr.getTR(), 2)
        self.assertAlmostEqual(1.48, atr.getATR(), 2)

        atr.addData(**next(i))
        self.assertAlmostEqual(0.97, atr.getTR(), 2)
        self.assertAlmostEqual(1.42, atr.getATR(), 2)

        atr.addData(**next(i))
        self.assertAlmostEqual(1.44, atr.getTR(), 2)
        self.assertAlmostEqual(1.42, atr.getATR(), 2)

        atr.addData(**next(i))
        self.assertAlmostEqual(1.10, atr.getTR(), 2)
        self.assertAlmostEqual(1.38, atr.getATR(), 2)

        atr.addData(**next(i))
        self.assertAlmostEqual(1.72, atr.getTR(), 2)
        self.assertAlmostEqual(1.42, atr.getATR(), 2)

        atr.addData(**next(i))
        self.assertAlmostEqual(2.88, atr.getTR(), 2)
        self.assertAlmostEqual(1.61, atr.getATR(), 2)

        atr.addData(**next(i))
        self.assertAlmostEqual(2.04, atr.getTR(), 2)
        self.assertAlmostEqual(1.66, atr.getATR(), 2)

        atr.addData(**next(i))
        self.assertAlmostEqual(1.07, atr.getTR(), 2)
        self.assertAlmostEqual(1.59, atr.getATR(), 2)
