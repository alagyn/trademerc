import unittest
from .data import S_TEST_DATA

from cash_money.stats.ema import EMA


class EMATest(unittest.TestCase):
    def test_7Day(self):
        ema = EMA(period=7, smoothing=2)

        self.assertEqual(0.0, ema.getValue())

        i = iter(S_TEST_DATA)

        self.assertEqual(0.1, ema.next(next(i)))
        self.assertAlmostEqual(0.125, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.169, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.252, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.239, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.304, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.303, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.427, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.545, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.659, ema.next(next(i)), 3)
        self.assertAlmostEqual(0.794, ema.next(next(i)), 3)
