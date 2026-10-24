import unittest
from wiki_equation_evidence_v074430 import equation_rank

class EquationPriorityTests(unittest.TestCase):
    def test_normalization_priority(self):
        self.assertGreater(equation_rank("|a|^2 + |b|^2 = 1"),0)
    def test_symbol_fragment_rejected(self):
        self.assertLess(equation_rank("alpha, beta"),0)
        self.assertLess(equation_rank("|0>"),0)
    def test_state_superposition(self):
        self.assertGreater(equation_rank(r"\alpha |0\rangle + \beta |1\rangle"),0)
if __name__=="__main__":
    unittest.main()
