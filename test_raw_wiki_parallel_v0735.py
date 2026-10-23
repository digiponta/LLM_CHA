import unittest
from raw_wiki_parallel_v0735 import parallel_evidence

class RawWikiParallelTests(unittest.TestCase):
    def test_found_preserves_original(self):
        raw="【原文中の関連記述・未検証】原文の記述"
        def lookup(term):
            self.assertEqual(term,"時間")
            return {"status":"FOUND","title":"時間","extract":"時間は物理学で用いられる概念。追加記述。","url":"https://ja.wikipedia.org/wiki/%E6%99%82%E9%96%93"}
        result=parallel_evidence(raw,"時間",lookup)
        self.assertTrue(result["answer"].startswith(raw))
        self.assertIn("【Wikipedia検索結果・外部情報・未検証】",result["answer"])
        self.assertIn("出典：https://ja.wikipedia.org/wiki/",result["answer"])
        self.assertFalse(result["auto_promote"])
    def test_missing_retains_raw(self):
        raw="未検証の宇宙記述"
        result=parallel_evidence(raw,"宇宙",lambda term:{"status":"NOT_FOUND"})
        self.assertEqual(result["answer"],raw)
    def test_ambiguous_retains_raw(self):
        result=parallel_evidence("原文","バベル",lambda term:{"status":"AMBIGUOUS"})
        self.assertEqual(result["answer"],"原文")
    def test_network_failure(self):
        def fail(term):raise TimeoutError()
        result=parallel_evidence("原文","時間",fail)
        self.assertEqual(result["answer"],"原文")
if __name__=="__main__":unittest.main()
