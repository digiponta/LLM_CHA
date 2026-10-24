import ast
import unittest
from pathlib import Path
from unittest.mock import patch
from wiki_expanded_aspect_v074426 import expanded_aspect

class RankingIntegrationTests(unittest.TestCase):
    def test_rank_called_for_expanded_article(self):
        short={"status":"FOUND","title":"量子力学","url":"https://ja.wikipedia.org/wiki/量子力学","extract":"概要。"}
        article="量子力学は現代物理学の根幹を成す理論として様々な研究で利用されている。量子力学の実験では粒子の状態を測定することによって理論上の予測を観測している。"
        with patch("wiki_expanded_aspect_v074426._request",return_value={"query":{"pages":[{"title":"量子力学","extract":article}]}}):
            answer=expanded_aspect(short,"実験")
        self.assertIn("粒子の状態を測定",answer["answer"])
        self.assertEqual(answer["ranking"],"ASPECT_LEXICAL_V1")
    def test_runtime_parses(self):
        source=Path(__file__).with_name("wiki_expanded_aspect_v074426.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("ranked_evidence",source)

if __name__=="__main__":unittest.main()
