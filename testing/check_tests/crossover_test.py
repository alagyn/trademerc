import unittest
from indicators.barValue import BarValue
from checks.crossoverCheck import CrossoverCheck


class CrossoverTest(unittest.TestCase):
    def test_crossover(self):
        bv = BarValue()
        co = CrossoverCheck(bv.low, bv.close, "up")

        bv.addData(0, 1, 0)

        co.check()
        self.assertFalse(co.check())

        bv.addData(1, 0, 0)

        self.assertTrue(co.check())
        self.assertFalse(co.check())

        bv.addData(0, 1, 0)

        self.assertFalse(co.check())

        bv.addData(1, 0, 0)

        self.assertTrue(co.check())
