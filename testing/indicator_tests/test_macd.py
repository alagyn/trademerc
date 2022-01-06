import unittest
from indicators.macd import MACD


class MACDTest(unittest.TestCase):
    def test_macd(self):
        macd = MACD(10, 20, 10)
        # TODO test macd
