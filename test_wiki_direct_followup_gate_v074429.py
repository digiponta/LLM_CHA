import unittest
from wiki_persona_multiturn_v0520 import WikiConversation

def context(text):
    return {"status":"FOUND","title":"シュレーディンガー方程式",
            "url":"https://ja.wikipedia.org/wiki/シュレーディンガー方程式",
            "extract":text}

class WikiDirectFollowupGateTests(unittest.TestCase):
    def test_skip_orphan_fragments(self):
        wiki=WikiConversation()
        wiki.offer(context("シュレーディンガー方程式は量子力学の基礎方程式である。"
            "名前はエルヴィン・シュレーディンガーにちなむ。"
            "シュレーディンガー方程式は、最も基本的な形では以下のように表される。"
            r"{\\displaystyle \\hbar }。"
            "はディラック定数、Ψ(x, t) は波動関数、ˆH は系のハミルトニアンである。"
            "状態ベクトルの時間発展は、シュレーディンガー方程式で表される。"))
        answer=wiki.respond("もっと詳しく")
        self.assertIn("状態ベクトルの時間発展",answer["answer"])
        self.assertNotIn("ディラック定数",answer["answer"])
    def test_only_fragments_returns_insufficient(self):
        wiki=WikiConversation()
        wiki.offer(context("シュレーディンガー方程式は量子力学の基礎方程式である。"
            "名前はエルヴィン・シュレーディンガーにちなむ。"
            r"{\\displaystyle \\hbar }。"))
        answer=wiki.respond("もっと詳しく")
        self.assertEqual(answer["route"],"WIKIPEDIA_EVIDENCE_INSUFFICIENT")
    def test_no_unsupported_learning(self):
        wiki=WikiConversation()
        wiki.offer(context("シュレーディンガー方程式は量子力学の基礎方程式である。"
            "状態ベクトルの時間発展は、シュレーディンガー方程式で表される。"))
        answer=wiki.respond("もっと詳しく")
        self.assertFalse(answer["train_ready"])

if __name__=="__main__":
    unittest.main()
