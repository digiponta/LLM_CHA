import unittest
from wikipedia_relation_evidence_v0621 import article_evidence

def lookup(term):
    return {"status":"FOUND","title":"架空自動車","url":"https://ja.wikipedia.org/wiki/X",
            "extract":"架空自動車は会社。"}

def fetch(params):
    if params.get("action")=="query":
        return {"query":{"pages":[{"extract":"架空自動車は日本の企業である。"}]}}
    if params.get("prop")=="sections":
        return {"parse":{"sections":[{"index":"1","line":"沿革"}]}}
    if params.get("prop")=="wikitext":
        return {"parse":{"wikitext":{"*":"== 沿革 ==\n1937年に企業として設立された記録が残っている。"}}}
    raise ValueError("unexpected request")

class HistorySectionTests(unittest.TestCase):
    def test_fallback_to_history_section(self):
        result=article_evidence("架空自動車","歴史",lookup,fetch)
        self.assertEqual(result["status"],"FOUND")
        self.assertIn("1937年",result["answer"])
        self.assertEqual(result["truth_state"],"EXTERNAL_UNVERIFIED")
    def test_other_attribute_unavailable(self):
        self.assertEqual(article_evidence("架空自動車","営業時間",lookup,fetch)["status"],"INSUFFICIENT")

if __name__=="__main__":
    unittest.main()
