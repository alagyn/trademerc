import unittest
from cash_money.checks.crossoverCheck import CrossoverCheck
from testFunc import TestFunc


class CrossoverTest(unittest.TestCase):
    def test_crossover(self):
        low = TestFunc(0)
        close = TestFunc(0)

        coU = CrossoverCheck(low, close, "up")
        coD = CrossoverCheck(low, close, 'down')

        low.v = 0
        close.v = 1

        coU.update(True)
        coD.update(True)

        coU.update(False)
        self.assertFalse(coU.check(), "UP No change 1")
        coD.update(False)
        self.assertFalse(coD.check(), "DN No change 1")

        low.v = 1
        close.v = 0

        coU.update(False)
        self.assertTrue(coU.check(), 'CU 1.U')
        coD.update(False)
        self.assertFalse(coD.check(), 'CU 1.D')
        coU.update(False)
        self.assertFalse(coU.check(), 'CU 1.U2')

        low.v = 0
        close.v = 1

        coU.update(False)
        self.assertFalse(coU.check(), 'CD 1.U')
        coD.update(False)
        self.assertTrue(coD.check(), 'CD 1.D1')
        coU.update(False)
        self.assertFalse(coU.check(), 'CD 1.D2')

        low.v = 1
        close.v = 0
        coU.update(False)
        self.assertTrue(coU.check(), 'CU 2.U')
        coD.update(False)
        self.assertFalse(coD.check(), 'CU 2.D')
