import unittest
from equation_semantic_evidence_v074437 import equation_meaning
from wiki_equation_evidence_v074430 import EquationCursor

class MeaningTests(unittest.TestCase):
    def test_missing_is_safe(self):
        self.assertIsNone(equation_meaning({"title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット"},[]))
    def test_cursor_once(self):
        c=EquationCursor()
        self.assertIsNone(c.explain_once({"title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット"}))
    def test_wrong_subject(self):
        self.assertIsNone(equation_meaning({"title":"CPU","url":"https://ja.wikipedia.org/wiki/CPU"},[]))

if __name__=="__main__":
    unittest.main()
