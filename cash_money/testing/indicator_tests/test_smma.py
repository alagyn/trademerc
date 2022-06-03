import unittest
from cash_money.indicators.smma import SoloSMMA
from .data import S_TEST_DATA


class SMMATest(unittest.TestCase):
    def test_smma(self):
        smma = SoloSMMA(5)

        expected = [
            0.1, 0.12, 0.16, 0.22, 0.22, 0.28,
            0.28, 0.38, 0.49, 0.59, 0.71, 0.75,
            0.78, 0.78, 0.85, 0.98, 1.06
        ]

        for e, data in zip(expected, S_TEST_DATA):
            a = smma.next(data)

            self.assertAlmostEqual(e, a, 2)