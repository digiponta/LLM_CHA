import unittest
from wiki_equation_evidence_v074430 import math_blocks,EquationCursor

WIKI={"status":"FOUND","title":"シュレーディンガー方程式",
      "url":"https://ja.wikipedia.org/wiki/シュレーディンガー方程式"}
RAW=r"時間に依存する方程式は次の形で記述される。<math>i\hbar\frac{\partial}{\partial t}\Psi=\hat H\Psi</math>"

def fetch(url):
    return {"query":{"pages":[{"title":WIKI["title"],"revisions":[
        {"slots":{"main":{"content":RAW}}}]}]}}

class EquationTests(unittest.TestCase):
    def test_source_exact(self):
        x=math_blocks(WIKI,fetch)
        self.assertEqual(len(x),1)
        self.assertIn(r"\frac",x[0]["latex"])
        self.assertFalse(x[0]["train_ready"])
    def test_cursor_dedup(self):
        c=EquationCursor()
        self.assertIn("LATEX(",c.next(WIKI,fetch)["answer"])
        self.assertIsNone(c.next(WIKI,fetch))
    def test_identity_reset(self):
        c=EquationCursor()
        self.assertIsNotNone(c.next(WIKI,fetch))
        c.reset()
        self.assertIsNotNone(c.next(WIKI,fetch))
    def test_missing(self):
        self.assertEqual(math_blocks({"status":"FOUND","title":"x","url":"http://bad"},fetch),[])
    def test_reject_unsafe(self):
        def malicious(url):
            return {"query":{"pages":[{"title":WIKI["title"],"revisions":[{"slots":{"main":{"content":r"<math>\input{file}=x</math>"}}}]}]}}
        self.assertEqual(math_blocks(WIKI,malicious),[])
if __name__=="__main__":unittest.main()
