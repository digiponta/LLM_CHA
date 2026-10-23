import unittest
from wiki_math_integrity_v074421 import has_missing_math_operand, safe_evidence_sentence

class MathIntegrityTests(unittest.TestCase):
    def test_wavefunction_removed(self):
        self.assertTrue(has_missing_math_operand("状態ベクトル   （もしくは波動関数   ）で記述される"))
    def test_state_removed(self):
        self.assertTrue(has_missing_math_operand("状態   と別の状態   で次のような状態   を作る"))
    def test_normal_prose(self):
        self.assertFalse(has_missing_math_operand("量子力学では状態ベクトルで系を記述する"))
    def test_regular_phrase(self):
        self.assertTrue(safe_evidence_sentence("量子力学では複数の状態の重ね合わせを考える"))
    def test_nonstring(self):
        self.assertFalse(safe_evidence_sentence(None))

if __name__=="__main__":
    unittest.main()
