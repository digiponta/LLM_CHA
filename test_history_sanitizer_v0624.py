import unittest
from wikipedia_relation_evidence_v0621 import article_evidence

def lookup(term):
    return {"status":"FOUND","title":"例示自動車","url":"https://ja.wikipedia.org/wiki/Example","extract":"企業の説明。"}

def fetch(params):
    if params.get("action")=="query":
        return {"query":{"pages":[{"extract":"例示自動車は自動車メーカー。"}]}}
    if params.get("prop")=="sections":
        return {"parse":{"sections":[{"index":"1","line":"歴史"}]}}
    if params.get("prop")=="wikitext":
        return {"parse":{"wikitext":{"*":"== 歴史 ==\n</ref> と工場の閉鎖に関する記述がある。\n1937年に企業として設立された記録が残っている。"}}}
    raise AssertionError(params)

class HistorySanitizerTests(unittest.TestCase):
    def test_reject_broken_ref(self):
        result=article_evidence("例示自動車","歴史",lookup,fetch)
        self.assertEqual(result["status"],"FOUND")
        self.assertIn("1937年",result["answer"])
        self.assertNotIn("</ref>",result["answer"])
    def test_no_clean_text_fails_closed(self):
        def broken(params):
            if params.get("prop")=="wikitext":
                return {"parse":{"wikitext":{"*":"== 歴史 ==\n</ref> と工場の閉鎖に関する記述がある。"}}}
            return fetch(params)
        self.assertEqual(article_evidence("例示自動車","歴史",lookup,broken)["status"],"INSUFFICIENT")
if __name__=="__main__":unittest.main()
