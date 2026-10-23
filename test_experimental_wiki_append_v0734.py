import unittest
from experimental_wiki_append_v0734 import append_wikipedia,term_from_question

class ExperimentalWikiAppendTests(unittest.TestCase):
    def test_term(self):
        self.assertEqual(term_from_question("量子力学とは何ですか？"),"量子力学")
    def test_found(self):
        wiki={"status":"FOUND","title":"量子力学","extract":"量子力学は物理学の理論である。追加文。","url":"https://ja.wikipedia.org/wiki/量子力学"}
        out=append_wikipedia("【未承認・候補知識】実験回答","量子力学とは",lookup=lambda t:wiki)
        self.assertEqual(out["wiki_status"],"APPENDED")
        self.assertTrue(out["answer"].startswith("【未承認・候補知識】実験回答"))
        self.assertIn("外部情報・未検証",out["answer"])
        self.assertFalse(out["auto_promote"])
    def test_not_found(self):
        out=append_wikipedia("未承認回答","未知の語",lookup=lambda t:{"status":"NOT_FOUND"})
        self.assertEqual(out["answer"],"未承認回答")
    def test_ambiguous(self):
        out=append_wikipedia("候補","バベル",lookup=lambda t:{"status":"AMBIGUOUS"})
        self.assertEqual(out["wiki_status"],"AMBIGUOUS")
    def test_invalid_url(self):
        out=append_wikipedia("候補","語",lookup=lambda t:{"status":"FOUND","title":"X","extract":"Text","url":"https://example.com"})
        self.assertEqual(out["wiki_status"],"INVALID_EVIDENCE")
    def test_lookup_failure(self):
        def broken(t):raise TimeoutError("no network")
        out=append_wikipedia("候補","語",lookup=broken)
        self.assertEqual(out["answer"],"候補")
        self.assertEqual(out["wiki_status"],"LOOKUP_FAILED")
if __name__=="__main__":unittest.main()
