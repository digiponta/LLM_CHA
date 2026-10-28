import unittest
from ingest_wikipedia_foundation_v013586 import article_partition,sentences,ingest

class WikiIngestionTests(unittest.TestCase):
    def test_deterministic_partition(self):
        self.assertEqual(article_partition(12345),article_partition(12345))
    def test_sentence_filter(self):
        data=sentences("短い。これは日本語基礎学習用の比較的長い文章です。",min_chars=12)
        self.assertEqual(len(data),1)
    def test_article_disjoint(self):
        ids=list(range(100,140))
        pages={str(i):{"pageid":i,"title":str(i),"url":"https://ja.wikipedia.org/",
             "revision_id":1,"revision_timestamp":"2026-10-28T00:00:00Z",
             "extract":"これは文章を検証するための日本語テキストです。"} for i in ids}
        train,ev,manifest=ingest(list(pages),lambda title:pages[title])
        self.assertFalse({x["pageid"] for x in train}&{x["pageid"] for x in ev})
        self.assertEqual(len(manifest),40)
    def test_redirect_dedup_by_id(self):
        def get(title):
            return {"pageid":12,"title":"同一記事","url":"https://ja.wikipedia.org/",
               "revision_id":1,"revision_timestamp":"now",
               "extract":"これは十分に長い日本語の文章であり、学習用に抽出できる。"}
        train,ev,manifest=ingest(["A","B"],get)
        self.assertEqual(len(manifest),1)
    def test_missing_article(self):
        train,ev,manifest=ingest(["missing"],lambda _:None)
        self.assertEqual((train,ev),([],[]))
        self.assertEqual(manifest[0]["status"],"MISSING_OR_EMPTY")

if __name__=="__main__":
    unittest.main()
