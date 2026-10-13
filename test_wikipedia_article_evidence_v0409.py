import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from external_candidate_store_v0407 import ingest
from test_external_candidate_store_v0407 import report
from wikipedia_article_evidence_v0409 import parse_article,inspect,fetch_article

class ArticleEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.source=Path(self.tmp.name)/"source.json"
        self.store=Path(self.tmp.name)/"store.json"
        self.source.write_text(json.dumps(report(),ensure_ascii=False),encoding="utf-8")
        ingest(self.source,self.store)
        self.candidate=json.loads(self.store.read_text(encoding="utf-8"))["records"][0]
    def tearDown(self):self.tmp.cleanup()
    def response(self,title="小説",extract="小説は文学作品の形式。",revid=987):
        return {"query":{"pages":[{"title":title,"pageid":123,"revisions":[{"revid":revid}],"extract":extract}]}}
    def test_article_metadata(self):
        x=parse_article(self.response(),self.candidate,"t")
        self.assertEqual(x["pageid"],123)
        self.assertEqual(x["revid"],987)
        self.assertEqual(x["article_title"],"小説")
        self.assertEqual(len(x["extract_sha256"]),64)
        self.assertEqual(x["factual_truth"],"UNVERIFIED")
    def test_not_training_or_truth(self):
        x=parse_article(self.response(),self.candidate,"t")
        self.assertFalse(x["eligible_for_training"])
        self.assertFalse(x["revision_content_verified"])
        self.assertEqual(x["semantic_memory_writes"],0)
        self.assertEqual(x["truth_promotions"],0)
    def test_wrong_title(self):
        with self.assertRaises(ValueError):
            parse_article(self.response(title="小説家"),self.candidate,"t")
    def test_missing_extract(self):
        with self.assertRaises(ValueError):
            parse_article(self.response(extract=""),self.candidate,"t")
    def test_missing_revision(self):
        with self.assertRaises(ValueError):
            parse_article(self.response(revid=None),self.candidate,"t")
    def test_missing_article(self):
        with self.assertRaises(ValueError):
            parse_article({"query":{"pages":[{"missing":True}]}},self.candidate,"t")
    def test_stale_hash_rejected(self):
        with self.assertRaises(ValueError):
            inspect(self.store,self.candidate["id"],"0"*64)
    def test_nonexistent_id_rejected(self):
        with self.assertRaises(ValueError):
            inspect(self.store,"0"*24,self.candidate["content_sha256"])
    def test_mocked_fetch(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*a):return False
            def read(self,n):return json.dumps(self_obj.response(),ensure_ascii=False).encode("utf-8")
        self_obj=self
        with patch("wikipedia_article_evidence_v0409.urlopen",return_value=Response()) as fn:
            x=fetch_article(self.candidate)
        self.assertEqual(x["revid"],987)
        self.assertIn("exintro=1",fn.call_args.args[0].full_url)
    def test_no_write_to_store(self):
        before=self.store.read_bytes()
        with patch("wikipedia_article_evidence_v0409.fetch_article",return_value={"test":True}):
            inspect(self.store,self.candidate["id"],self.candidate["content_sha256"])
        self.assertEqual(before,self.store.read_bytes())
if __name__=="__main__":unittest.main()
