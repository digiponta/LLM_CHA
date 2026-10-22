import unittest
from wikipedia_relation_evidence_v0621 import resolve_entity,article_evidence

def wiki(term):
    if term=="トヨタ":return {"status":"AMBIGUOUS","candidates":["トヨタ自動車","トヨタ"]}
    return {"status":"FOUND","title":term,"url":"https://ja.wikipedia.org/wiki/"+term,"extract":"日本の企業。"}

def req(params):
    return {"query":{"pages":[{"extract":"これは企業の説明。\n本社は愛知県豊田市に置かれている。\n会社の歴史と創業について記述されている。"}]}}

class EvidenceTests(unittest.TestCase):
    def test_alias(self):
        self.assertEqual(resolve_entity("トヨタ",wiki)["title"],"トヨタ自動車")
    def test_history(self):
        a=article_evidence("トヨタ","歴史",wiki,req)
        self.assertEqual(a["status"],"FOUND")
        self.assertIn("歴史",a["answer"])
    def test_location(self):
        a=article_evidence("トヨタ","所在地",wiki,req)
        self.assertEqual(a["status"],"FOUND")
        self.assertIn("本社",a["answer"])
    def test_no_unsupported_answer(self):
        a=article_evidence("トヨタ","メニュー",wiki,req)
        self.assertEqual(a["status"],"INSUFFICIENT")
    def test_unresolved_ambiguity(self):
        self.assertEqual(resolve_entity("不明",lambda t:{"status":"AMBIGUOUS"})["status"],"AMBIGUOUS")
if __name__=="__main__":unittest.main()
