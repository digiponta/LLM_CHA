import unittest
from diagnose_daily_teacher_forcing_v013588287 import first_divergence
class TeacherForcingTests(unittest.TestCase):
    def test_first_token(self):self.assertEqual(first_divergence([1,2,3],[9,2,3]),0)
    def test_later_token(self):self.assertEqual(first_divergence([1,2,3],[1,2,4]),2)
    def test_shorter_generation(self):self.assertEqual(first_divergence([1,2,3],[1,2]),2)
    def test_exact(self):self.assertIsNone(first_divergence([1,2,3],[1,2,3]))
    def test_eos_difference(self):self.assertEqual(first_divergence([1,2,3],[1,2,5]),2)
if __name__=="__main__":unittest.main()
