import unittest
from wikipedia_answer_prefix_v04141 import format_wiki_answer,from_article_alignment

URL="https://ja.wikipedia.org/wiki/%E5%B0%8F%E8%AA%AC"
def render(**kwargs):
    options=dict(source="WIKIPEDIA_EXTRACTIVE_CANDIDATE",article_url=URL,
                 factual_truth="UNVERIFIED",eligible_for_training=False,
                 explicit_source_request=True)
    options.update(kwargs)
    return format_wiki_answer("小説は文学の形式の一つである。",**options)

class WikiPrefixTests(unittest.TestCase):
    def test_wiki_prefix(self):self.assertTrue(render().startswith("wiki> "))
    def test_source_url(self):self.assertIn("出典: "+URL,render())
    def test_unverified_label(self):self.assertIn("未検証",render())
    def test_no_automatic_response(self):
        with self.assertRaises(ValueError):render(explicit_source_request=False)
    def test_non_wiki_source(self):
        with self.assertRaises(ValueError):render(source="PERSONA_STATEMENT")
    def test_non_wiki_domain(self):
        with self.assertRaises(ValueError):render(article_url="https://example.com/wiki/x")
    def test_forged_domain(self):
        with self.assertRaises(ValueError):render(article_url="https://ja.wikipedia.org.evil.invalid/wiki/x")
    def test_truth_override(self):
        with self.assertRaises(ValueError):render(factual_truth="TRUE")
    def test_training_override(self):
        with self.assertRaises(ValueError):render(eligible_for_training=True)
    def test_double_prefix(self):
        with self.assertRaises(ValueError):
            format_wiki_answer("wiki> test",source="WIKIPEDIA_SEARCH_RESULT",article_url=URL,
                               factual_truth="UNVERIFIED",explicit_source_request=True)
    def test_alignment(self):
        p={"proposition_literal":"小説は文学である。","factual_truth":"UNVERIFIED",
           "eligible_for_training":False,"review_state":"PENDING_REVIEW"}
        a={"version":"v0.4.12","propositions":[p],"article_url":URL,
           "truth_promotions":0,"semantic_memory_writes":0,"training_enabled":False}
        self.assertTrue(from_article_alignment(p,a,explicit_source_request=True).startswith("wiki> "))
if __name__=="__main__":unittest.main()
