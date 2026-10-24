import unittest
from wiki_equation_evidence_v074430 import math_blocks, EquationCursor
from gui_latex_v062 import split_latex

W={"status":"FOUND","title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット"}
def fetch(raw):
    return lambda url:{"query":{"pages":[{"title":"量子ビット","revisions":[{"slots":{"main":{"content":raw}}}]}]}}
class EquationLabelTests(unittest.TestCase):
    def test_dangling_intro_rejected(self):
        s=r"ブラ-ケット記法では、1量子ビットは、<math>\alpha|0\rangle+\beta|1\rangle</math>"
        blocks=math_blocks(W,fetch(s))
        self.assertEqual(blocks[0]["description"],"")
    def test_deictic_label_rejected(self):
        s=r"これを観測した際、状態：<math>|0\rangle</math>"
        blocks=math_blocks(W,fetch(s))
        self.assertTrue(not blocks or blocks[0]["description"]=="")
    def test_source_text_retained(self):
        s=r"<math>\alpha |0\rangle + \beta |1\rangle</math>"
        a=EquationCursor().next(W,fetch(s))
        self.assertIsNotNone(a)
        self.assertIn("[数式原文:",a["answer"])
    def test_nested_marker_split(self):
        t=r"AI: LATEX( \Psi(x,t)=\alpha(x)+\beta(t) ) [数式原文: \Psi(x,t)]"
        parsed=split_latex(t)
        self.assertEqual(sum(is_math for is_math,_ in parsed),1)
        self.assertIn(r"\beta(t)",[content for kind,content in parsed if kind][0])
if __name__=="__main__":unittest.main()
