import unittest
from explicit_topic_corpus_v0941 import corpus_mentions
from context_aware_response_v095 import ContextualResponse

class SelectedWikiCorpusTests(unittest.TestCase):
    def test_memory_corpus_found(self):
        corpus=("サーバ仮想化に対応したCPUでは、仮想メモリのアドレスに識別番号が追加される。\n"
                "実行中の命令が保持されるメモリのアドレス値をたどる。")
        hits=corpus_mentions("メモリ",corpus)
        self.assertEqual(len(hits),2)
        state=ContextualResponse()
        state.set_topic("メモリ","NAGATO_CORPUS",hits)
        response=state.respond("貴方はどう思う？")
        self.assertEqual(response["topic"],"メモリ")
        self.assertIn("仮想メモリ",response["answer"])
        self.assertNotIn("量子力学",response["answer"])
    def test_no_evidence_preserves_wikipedia_context(self):
        state=ContextualResponse()
        state.set_topic("メモリ","WIKIPEDIA_SELECTED",[])
        answer=state.respond("貴方はどう思う？")
        self.assertIn("メモリ",answer["answer"])
    def test_unrelated_subject_not_imported(self):
        self.assertEqual(corpus_mentions("メモリ","数学は、文学の分類。"),[])
if __name__=="__main__":
    unittest.main()
