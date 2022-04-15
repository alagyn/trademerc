import unittest
from indicators.barValue import BarValue
from checks.crossoverCheck import CrossoverCheck
from objects.bar import Bar


class CrossoverTest(unittest.TestCase):
    def test_crossover(self):
        bv = BarValue()
        coU = CrossoverCheck(bv.low, bv.close, "up")
        coD = CrossoverCheck(bv.low, bv.close, 'down')

        bar = Bar(0, 1, 0)
        bv.addData(bar)

        self.assertFalse(coU.update(False), "Init")
        self.assertFalse(coU.update(False), "Init")

        self.assertFalse(coD.update(False), "No change 1")
        self.assertFalse(coD.update(False), "No change 1")

        bar = Bar(1, 0, 0)
        bv.addData(bar)

        self.assertTrue(coU.update(False), 'CU 1.a')
        self.assertFalse(coU.update(False), 'CU 1.b')

        self.assertFalse(coD.update(False), 'CU 1')

        bar = Bar(0, 1, 0)
        bv.addData(bar)

        self.assertFalse(coU.update(False), 'CD 1')

        self.assertTrue(coD.update(False), 'CD 1.a')
        self.assertFalse(coD.update(False), 'CD 1.b')

        bar = Bar(1, 0, 0)
        bv.addData(bar)

        self.assertTrue(coU.update(False), 'CU 2')
        self.assertFalse(coD.update(False), 'CU 2')
