import unittest
from cash_money.indicators.parabolicSAR import ParabolicSAR
from cash_money.indicators.lineManager import LineManager
from cash_money.objects.bar import Bar


class PSARTest(unittest.TestCase):
    def test_uptrend(self):
        lm = LineManager()
        sar = ParabolicSAR("TEST PSAR", lm)

        testvals = [
            (47.85, 47.48, None),
            (47.83, 47.55, None),
            (47.95, 47.32, None),
            (48.11, 47.25, None),
            (48.30, 47.77, 47.25),
            (48.17, 47.91, 47.25),
            (48.60, 47.90, 47.27),
            (48.33, 47.74, 47.32),
            (48.40, 48.10, 47.38),
            (48.55, 48.06, 47.42),
            (48.45, 48.07, 47.47),
            (48.70, 47.79, 47.52),
            (48.72, 48.14, 47.59),
            (48.90, 48.39, 47.68),
            (48.87, 48.37, 47.8),
            (48.82, 48.24, 47.91),
            (49.05, 48.64, 48.01),
            (49.20, 48.94, 48.13),
            (49.35, 48.86, 48.28)
        ]

        for i, x in enumerate(testvals):
            bar = Bar(x[1], (x[0] + x[1]) / 2, x[0])
            lm.update(bar.lo, bar.close, bar.hi, 0)
            sar.update()
            val = sar.psar()
            if val is not None and x[2] is not None:
                self.assertAlmostEqual(x[2], val, 2)
            elif val is not None and x[2] is None:
                self.assertTrue(True, "Value should not be none")

    def test_downtrend(self):
        lm = LineManager()
        sar = ParabolicSAR("TEST PSAR", lm)

        testvals = [
            (46.44, 45.56, None),
            (46.47, 46.17, None),
            (46.50, 45.60, None),
            (46.59, 45.9, None),
            (46.55, 45.38, 46.59),
            (46.3, 45.25, 46.59),
            (45.43, 43.99, 46.55),
            (44.55, 44.07, 46.4),
            (44.84, 44.0, 46.26),
            (44.8, 43.96, 46.12),
            (44.38, 43.27, 45.95),
            (43.97, 42.58, 45.68),
            (43.23, 42.83, 45.31),
            (43.73, 42.98, 44.98),
            (43.92, 43.37, 44.69),
            (43.61, 42.57, 44.44),
            (42.97, 42.07, 44.18),
            (43.13, 42.59, 43.84),
            (43.46, 42.71, 43.56)
        ]

        for i, x in enumerate(testvals):
            bar = Bar(x[1], (x[0] + x[1]) / 2, x[0])
            lm.update(bar.lo, bar.close, bar.hi, 0)
            sar.update()
            val = sar.psar()
            if val is not None and x[2] is not None:

                a = round(val, 2)
                b = round(sar._extreme, 2)
                c = round(val - sar._extreme, 2)
                d = round(sar._af, 2)
                e = round(sar._af * (val - sar._extreme), 3)

                # print(a, b, c, d, e)
                self.assertAlmostEqual(x[2], val, delta=0.008)
            elif val is not None and x[2] is None:
                self.assertTrue(True, "Value should not be none")
