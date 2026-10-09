import unittest
from diagnose_generation_trajectory_v02281 import make_conditions

class TrajectoryTests(unittest.TestCase):
    def test_three_conditions(self):
        cs=make_conditions(list(range(20)),8)
        self.assertEqual([c[0] for c in cs],["free","first_k","first_half"])
        self.assertEqual([len(c[1]) for c in cs],[0,8,10])
    def test_short_reference(self):
        cs=make_conditions([1,2,3],8)
        self.assertEqual(len(cs[1][1]),3)
        self.assertEqual(len(cs[2][1]),1)
    def test_invalid(self):
        with self.assertRaises(ValueError):make_conditions([],8)
        with self.assertRaises(ValueError):make_conditions([1],0)

if __name__=="__main__":unittest.main()
