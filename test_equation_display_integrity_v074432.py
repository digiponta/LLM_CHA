import unittest
from wiki_equation_evidence_v074430 import EquationCursor
from wiki_persona_multiturn_v0520 import WikiConversation

W={"status":"FOUND","title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット"}
def fetch(_url):
    return {"query":{"pages":[{"title":"量子ビット","revisions":[{"slots":{"main":{"content":r"<math>\\alpha|0\\rangle+\\beta|1\\rangle</math>"}}}]}]}}

class DisplayIntegrityTests(unittest.TestCase):
    def test_always_include_visible_tex_source(self):
        result=EquationCursor().next(W,fetch)
        self.assertIn("[数式原文:",result["answer"])
        self.assertIn("LATEX(",result["answer"])
    def test_no_dangling_intro(self):
        chat=WikiConversation()
        chat.offer({**W,"extract":"量子ビットは量子計算で用いられる情報の基本的な単位である。ブラ-ケット記法では、1量子ビットは、。量子ビットの状態は、測定により0か1の値になることがある。"})
        answer=chat.respond("もっと詳しく")
        self.assertNotIn("ブラ-ケット",answer["answer"])

if __name__=="__main__":unittest.main()
