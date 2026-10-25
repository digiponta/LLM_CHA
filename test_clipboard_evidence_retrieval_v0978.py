import unittest
from clipboard_evidence_retrieval_v0978 import retrieve,compare
TEXT="""スターバックス コーヒー ジャパン
パンプキン スパイス ラテ
手しぼり栗のモンブラン
ブラックベリー ヨーグルト フラペチーノ
キャラメル マキアート
ニューヨークチーズケーキ
"""
class ClipboardRetrievalTests(unittest.TestCase):
    def test_frappe_rank(self):
        hits=retrieve("フラペチーノの種類",TEXT)
        self.assertIn("フラペチーノ",hits[0]["text"])
    def test_keyword_baseline(self):
        self.assertTrue(retrieve("モンブラン",TEXT,method="keyword"))
    def test_not_llm_sem(self):
        self.assertEqual(compare("メニュー",TEXT)["semantic_vector"]["status"],"NOT_CONNECTED")
    def test_no_unrelated(self):
        self.assertEqual(retrieve("量子力学の交換関係",TEXT,min_score=.7),[])
    def test_empty(self):
        self.assertEqual(retrieve("",TEXT),[])
    def test_unverified(self):
        self.assertTrue(all(h["truth_state"]=="EXTERNAL_UNVERIFIED"
                            for h in retrieve("ラテ",TEXT)))
    def test_dedup(self):
        self.assertEqual(len(retrieve("モンブラン","手しぼり栗のモンブラン\n手しぼり栗のモンブラン")),1)
if __name__=="__main__":unittest.main()
