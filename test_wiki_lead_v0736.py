import unittest
from wiki_lead_v0736 import wiki_lead
from experimental_wiki_append_v0734 import append_wikipedia

class WikiLeadTests(unittest.TestCase):
    def test_parentheses(self):
        text="空間（くうかん、英: space。一般的な表現）とは、広がりを持つ領域である。次の文。"
        self.assertEqual(wiki_lead(text),"空間（くうかん、英: space。一般的な表現）とは、広がりを持つ領域である。")
    def test_incomplete(self):
        self.assertIsNone(wiki_lead("空間（くうかん、英: space）とは、。"))
    def test_short_valid(self):
        self.assertEqual(wiki_lead("時間は概念である。"),"時間は概念である。")
    def test_reject_empty(self):
        self.assertIsNone(wiki_lead(""))
    def test_append_fallback(self):
        result=append_wikipedia("原文","空間",lookup=lambda term:{
            "status":"FOUND","title":"空間",
            "extract":"空間（くうかん、英: space）とは、。",
            "url":"https://ja.wikipedia.org/wiki/空間"})
        self.assertEqual(result["wiki_status"],"EMPTY_EXTRACT")
        self.assertEqual(result["answer"],"原文")
if __name__=="__main__":unittest.main()
