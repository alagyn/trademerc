import unittest
from cash_money.indicators.macd import MACD
from cash_money.indicators.lineManager import LineManager


class MACDTest(unittest.TestCase):
    def test_macd(self):
        lm =LineManager()
        macd = MACD("TEST MACD", lm, 10, 20, 10)
        # TODO test macd
