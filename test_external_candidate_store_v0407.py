import json
import tempfile
import unittest
from pathlib import Path
from external_candidate_store_v0407 import ingest

def report(excerpt="説明",url="https://ja.wikipedia.org/wiki/%E5%B0%8F%E8%AA%AC"):
    return {"version":"v0.4.6","concept":"小説","source":"Wikipedia (ja)",
            "candidate_count":1,"truth_promotions":0,"semantic_memory_writes":0,
            "training_enabled":False,"candidates":[{
                "concept":"小説","title":"小説","description":"文学のジャンル",
                "search_excerpt":excerpt,"url":url,
                "source":"WIKIPEDIA_SEARCH_RESULT","factual_truth":"UNVERIFIED",
                "review_state":"PENDING_REVIEW","eligible_for_training":False,
                "is_full_article":False,"retrieved_at_utc":"2026-10-13T00:00:00+00:00"}]}

class CandidateStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.input=Path(self.temp.name)/"input.json"
        self.store=Path(self.temp.name)/"store.json"
        self.put()
    def tearDown(self):self.temp.cleanup()
    def put(self,data=None):self.input.write_text(json.dumps(report() if data is None else data,ensure_ascii=False),encoding="utf-8")
    def read(self):return json.loads(self.store.read_text(encoding="utf-8"))
    def test_first_ingest(self):
        r=ingest(self.input,self.store)
        self.assertEqual(r["added"],1)
        self.assertEqual(self.read()["records"][0]["review_state"],"PENDING_REVIEW")
    def test_idempotent(self):
        ingest(self.input,self.store)
        r=ingest(self.input,self.store)
        self.assertEqual(r["unchanged"],1)
        self.assertEqual(len(self.read()["records"]),1)
    def test_update_requires_rereview(self):
        ingest(self.input,self.store)
        self.put(report("更新された記述"))
        r=ingest(self.input,self.store)
        self.assertEqual(r["updated"],1)
        row=self.read()["records"][0]
        self.assertEqual(row["review_state"],"NEEDS_REREVIEW")
        self.assertEqual(len(row["history"]),1)
    def test_preserves_manual_status_on_identical_content(self):
        ingest(self.input,self.store)
        d=self.read()
        d["records"][0]["review_state"]="REJECTED"
        self.store.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
        ingest(self.input,self.store)
        self.assertEqual(self.read()["records"][0]["review_state"],"REJECTED")
    def test_rejects_ineligible_trusted_flag(self):
        d=report()
        d["candidates"][0]["eligible_for_training"]=True
        self.put(d)
        with self.assertRaises(ValueError):ingest(self.input,self.store)
        self.assertFalse(self.store.exists())
    def test_rejects_external_url(self):
        self.put(report(url="https://example.com/wiki/test"))
        with self.assertRaises(ValueError):ingest(self.input,self.store)
    def test_invalid_existing_store_preserved(self):
        self.store.write_text("invalid-json",encoding="utf-8")
        before=self.store.read_bytes()
        with self.assertRaises(ValueError):ingest(self.input,self.store)
        self.assertEqual(before,self.store.read_bytes())
    def test_source_unchanged(self):
        before=self.input.read_bytes()
        ingest(self.input,self.store)
        self.assertEqual(before,self.input.read_bytes())
    def test_no_promotion(self):
        r=ingest(self.input,self.store)
        self.assertEqual(r["semantic_memory_writes"],0)
        self.assertEqual(r["truth_promotions"],0)
        self.assertFalse(r["training_enabled"])
    def test_same_source_destination(self):
        with self.assertRaises(ValueError):ingest(self.input,self.input)
if __name__=="__main__":unittest.main()
