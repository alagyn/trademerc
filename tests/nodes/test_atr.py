import unittest

from cash_money.nodes.averageTrueRange import AverageTrueRange, PERIOD
from .data import DatamapIter, RAW_TEST_DATA

from nodepasta.testing.tester import Tester


class ATRTest(unittest.TestCase):

    def test_8Day(self):
        atrNode = AverageTrueRange()
        atrNode.args[PERIOD].value = 8
        atrNode.setup()

        self.assertEqual(8, atrNode._atr_smma._p)

        i = DatamapIter(atrNode, RAW_TEST_DATA)

        tester = Tester(atrNode)

        # ATR, TR
        # yapf: disable
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
        # yapf: enable

        # OUTPUTS
        # 0: ATR
        # 1: TR

        next(i)
        out = tester.test({})
        atr: float = out["ATR"]
        tr: float = out["TR"]
        self.assertIsNone(atr)
        self.assertIsNone(tr)

        for x in expected:
            next(i)
            out = tester.test({})
            atr: float = out["ATR"]
            tr: float = out["TR"]

            self.assertIsNotNone(atr)
            self.assertIsNotNone(tr)

            self.assertAlmostEqual(x[0], atr, places=2)
            self.assertAlmostEqual(x[1], tr, delta=0.005)
