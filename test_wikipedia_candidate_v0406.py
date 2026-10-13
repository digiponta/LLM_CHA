import unittest
from unittest.mock import patch
from wikipedia_candidate_v0406 import clean_snippet, parse_results, retrieve

class WikipediaCandidateTests(unittest.TestCase):
    def test_parser_source_and_status(self):
        d=parse_results({"pages":[{"title":"小説","description":"文学作品","excerpt":"<span class=\"searchmatch\">小説</span>の解説"}]},"小説","2026-10-13T00:00:00+00:00")
        self.assertEqual(d["candidate_count"],1)
        c=d["candidates"][0]
        self.assertEqual(c["title"],"小説")
        self.assertEqual(c["search_excerpt"],"小説の解説")
        self.assertEqual(c["factual_truth"],"UNVERIFIED")
        self.assertEqual(c["review_state"],"PENDING_REVIEW")
        self.assertFalse(c["eligible_for_training"])
        self.assertFalse(c["is_full_article"])
        self.assertEqual(d["semantic_memory_writes"],0)
    def test_empty(self):
        self.assertEqual(parse_results({"pages":[]},"不存在","t")["candidate_count"],0)
    def test_invalid_response(self):
        with self.assertRaises(ValueError):parse_results({"invalid":[]},"小説","t")
    def test_invalid_concept(self):
        for x in ("","\n","X"*101):
            with self.subTest(x=x):
                with self.assertRaises(ValueError):retrieve(x)
    def test_no_markup_or_html_in_excerpts(self):
        self.assertEqual(clean_snippet("a &amp; <b>b</b>"),"a & b")
    def test_limit_five(self):
        pages=[{"title":f"項目{i}"} for i in range(12)]
        self.assertEqual(parse_results({"pages":pages},"項目","t")["candidate_count"],5)
    def test_mocked_network_no_side_effect(self):
        import json
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,n):return json.dumps({"pages":[{"title":"小説"}]}).encode()
        with patch("wikipedia_candidate_v0406.urlopen",return_value=Response()) as mock:
            d=retrieve("小説")
        self.assertEqual(d["candidate_count"],1)
        self.assertIn("w/rest.php/v1/search/page",mock.call_args.args[0].full_url)
        self.assertFalse(d["training_enabled"])
if __name__=="__main__":unittest.main()
