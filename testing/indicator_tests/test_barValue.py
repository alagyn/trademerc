import unittest
from .data import RAW_TEST_DATA
from indicators.barValue import BarValue


class BarValueTest(unittest.TestCase):
    def test_bars(self):
        bv = BarValue()

        for x in RAW_TEST_DATA:
            bv.addData(*x)
            self.assertEqual(x[0], bv.low())
            self.assertEqual(x[1], bv.close())
            self.assertEqual(x[2], bv.high())