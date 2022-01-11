import unittest
from indicators.barValue import BarValue
from checks.crossoverCheck import CrossoverCheck


class CrossoverTest(unittest.TestCase):
    def test_crossover(self):
        bv = BarValue()
        coU = CrossoverCheck(bv.low, bv.close, "up")
        coD = CrossoverCheck(bv.low, bv.close, 'down')

        bv.addData(0, 1, 0)

        self.assertFalse(coU.update(), "Init")
        self.assertFalse(coU.update(), "Init")

        self.assertFalse(coD.update(), "No change 1")
        self.assertFalse(coD.update(), "No change 1")

        bv.addData(1, 0, 0)

        self.assertTrue(coU.update(), 'CU 1.a')
        self.assertFalse(coU.update(), 'CU 1.b')

        self.assertFalse(coD.update(), 'CU 1')

        bv.addData(0, 1, 0)

        self.assertFalse(coU.update(), 'CD 1')

        self.assertTrue(coD.update(), 'CD 1.a')
        self.assertFalse(coD.update(), 'CD 1.b')

        bv.addData(1, 0, 0)

        self.assertTrue(coU.update(), 'CU 2')
        self.assertFalse(coD.update(), 'CU 2')
