import unittest
from cash_money.nodes.crossoverNode import Crossover
from nodepasta.testing.tester import Tester

class CrossoverTest(unittest.TestCase):
    def test_crossover(self):
        co = Crossover()
        tester = Tester(co)


        out = tester.test({
            "A": 0,
            "B": 10
        })

        self.assertEqual(0, out['Delta'])

        out = tester.test({
            "A": 0,
            "B": 15
        })
        self.assertEqual(0, out['Delta'])

        out = tester.test({
            "A": 15,
            "B": 10
        })
        self.assertEqual(1, out['Delta'])

        out = tester.test({
            "A": 15,
            "B": 10
        })
        self.assertEqual(0, out['Delta'])

        out = tester.test({
            "A": 10,
            "B": 15
        })
        self.assertEqual(-1, out['Delta'])

        out = tester.test({
            "A": 15,
            "B": 10
        })
        self.assertEqual(1, out['Delta'])

        out = tester.test({
            "A": 15,
            "B": 10
        })
        self.assertEqual(0, out['Delta'])

