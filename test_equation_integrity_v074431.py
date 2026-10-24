import unittest
from gui_latex_v062 import split_latex
from wiki_equation_evidence_v074430 import complete_formula,math_blocks

WIKI={"status":"FOUND","title":"シュレーディンガー方程式",
      "url":"https://ja.wikipedia.org/wiki/シュレーディンガー方程式"}
def fetch_text(raw):
    return lambda url:{"query":{"pages":[{"title":WIKI["title"],
        "revisions":[{"slots":{"main":{"content":raw}}}]}]}}

class EquationIntegrityTests(unittest.TestCase):
    def test_gui_nested_parentheses(self):
        parsed=split_latex(r"数式： LATEX( i\hbar \partial_t \Psi(x,t)=\hat H\Psi(x,t) )。")
        self.assertEqual(len([x for x in parsed if x[0]]),1)
        self.assertTrue(parsed[1][1].endswith(r"\Psi(x,t)"))
        self.assertEqual(parsed[2][1],"。")
    def test_reject_leading_equal(self):
        self.assertFalse(complete_formula(r"= \hat{H}\Psi(\boldsymbol{x},t) )"))
    def test_reject_bare_tex(self):
        self.assertFalse(complete_formula(r"\hbar"))
    def test_valid_equation(self):
        self.assertTrue(complete_formula(r"i\hbar\partial_t\Psi(x,t)=\hat H\Psi(x,t)"))
    def test_ignore_incomplete_wikitext_math(self):
        raw=r"<math>=\hat H \Psi )</math><math>i\hbar\partial_t\Psi=\hat H\Psi</math>"
        blocks=math_blocks(WIKI,fetch=fetch_text(raw))
        self.assertEqual(len(blocks),1)
        self.assertTrue(blocks[0]["latex"].startswith("i"))
    def test_no_broken_description(self):
        raw="ここで   は虚数単位、<math>i\\hbar\\partial_t\\Psi=\\hat H\\Psi</math>"
        blocks=math_blocks(WIKI,fetch=fetch_text(raw))
        self.assertEqual(blocks[0]["description"],"")

if __name__=="__main__": unittest.main()
