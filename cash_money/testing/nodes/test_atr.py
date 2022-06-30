import unittest

from cash_money.nodes.averageTrueRange import AverageTrueRange, PERIOD
from .data import DatamapIter, RAW_TEST_DATA


class ATRTest(unittest.TestCase):
    def test_8Day(self):
        atrNode = AverageTrueRange()
        atrNode.args[PERIOD].value = 8
        atrNode.setup()

        self.assertEqual(8, atrNode._atr_smma._p)

        i = DatamapIter(atrNode, RAW_TEST_DATA)

        # ATR, TR
        expected = [
            (1.68, 1.68),
            (1.565, 0.76),
            (1.584, 1.72),
            (1.48, 0.77),
            (1.42, 0.97),
            (1.42, 1.44),
            (1.38, 1.10),
            (1.42, 1.72),
            (1.61, 2.88),
            (1.66, 2.04),
            (1.59, 1.07)
        ]

        # OUTPUTS
        # 0: ATR
        # 1: TR

        atr = atrNode.atrOut
        tr = atrNode.trOut

        next(i)
        atrNode.execute()
        self.assertIsNone(atr.value)
        self.assertIsNone(tr.value)

        for x in expected:
            next(i)
            atrNode.execute()
            self.assertIsNotNone(atr.value)
            self.assertIsNotNone(tr.value)
            self.assertAlmostEqual(x[0], atr.value, places=2)
            self.assertAlmostEqual(x[1], tr.value, delta=0.005)
