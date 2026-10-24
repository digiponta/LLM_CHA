import unittest
from wiki_equation_evidence_v074430 import EquationCursor
W={"status":"FOUND","title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット"}
RAW=r"<math>\alpha |0\rangle + \beta |1\rangle</math><math>|\alpha|^2 + |\beta|^2 = 1</math>"
def fetch(url):
    return {"query":{"pages":[{"title":"量子ビット","revisions":[{"slots":{"main":{"content":RAW}}}]}]}}
class GroupedQubitEquations(unittest.TestCase):
    def test_two_equations_one_response(self):
        cursor=EquationCursor()
        answer=cursor.next(W,fetch)
        self.assertEqual(len(answer["blocks"]),2)
        self.assertEqual(answer["answer"].count("[数式原文:"),2)
        self.assertIsNone(cursor.next(W,fetch))
    def test_unverified_and_not_trainable(self):
        value=EquationCursor().next(W,fetch)
        self.assertFalse(value["train_ready"])
        self.assertEqual(value["truth_state"],"EXTERNAL_UNVERIFIED")
if __name__=="__main__":unittest.main()
