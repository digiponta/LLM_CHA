import unittest
from diagnose_teacher_forcing_v01324 import first_divergence

class TeacherForcingTests(unittest.TestCase):
    def test_identical(self):
        self.assertIsNone(first_divergence([1,2,3],[1,2,3]))
    def test_first_token(self):
        self.assertEqual(first_divergence([1,2,3],[4,2,3]),0)
    def test_later_token(self):
        self.assertEqual(first_divergence([1,2,3],[1,2,4]),2)
    def test_shorter_output(self):
        self.assertEqual(first_divergence([1,2,3],[1,2]),2)

if __name__=="__main__":
    unittest.main()
