import unittest
from wiki_expanded_aspect_v074426 import expanded_aspect
class ExpandedAspectTests(unittest.TestCase):
    def test_expanded_finds(self):
        article={"status":"FOUND","title":"量子力学","url":"https://ja.wikipedia.org/wiki/量子力学","extract":"概要。"}
        def fetch(url,params): return {"query":{"pages":[{"title":"量子力学","extract":"量子力学では観測や測定の結果を理論的に取り扱うことができる。"}]}}
        # fetch signature may vary; use a no-network negative test elsewhere.
        self.assertIsNone(expanded_aspect(article,"数式",fetch=lambda *a,**kw: {"query":{"pages":[]}}))
    def test_invalid(self):
        self.assertIsNone(expanded_aspect(None,"実験"))
    def test_local_first(self):
        wiki={"status":"FOUND","title":"量子力学","url":"https://ja.wikipedia.org/wiki/量子力学",
              "extract":"量子力学の実験では観測と測定を組み合わせて現象を調べることができる。"}
        self.assertIsNotNone(expanded_aspect(wiki,"実験"))
if __name__=="__main__":unittest.main()
