import json,tempfile,unittest
from pathlib import Path
from safe_semantic_registration_v013588273 import store_status,plan,register

C={"id":"sense-x","subject":"光電効果","meaning":"電子を放出する現象である",
"quality_gate":"PASS","review_status":"PENDING_HUMAN_REVIEW","source_url":"https://example.invalid",
"evidence_sentence":"光電効果とは電子を放出する現象である。"}
R={"decision":"APPROVE","human_review_recorded":True,"reviewer":"human",
"note":"checked source","subject":C["subject"],"meaning":C["meaning"],
"evidence_sentence":C["evidence_sentence"],"source_url":C["source_url"]}

class SafeRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        d=Path(self.tmp.name)
        self.paths={name:str(d/(name+".jsonl")) for name in ("atomic","subject_index","typed_index","unified","truth")}
        self.provenance=d/"provenance.json"
        for path in self.paths.values():Path(path).write_text("",encoding="utf-8")
        self.provenance.write_text("[]",encoding="utf-8")
        self.quality={"candidates":[dict(C)]}
        self.reviews={"sense-x":dict(R)}
    def tearDown(self):self.tmp.cleanup()
    def test_missing_distinct_from_empty(self):
        Path(self.paths["unified"]).unlink()
        status=store_status(self.paths)
        self.assertEqual(status["atomic"]["status"],"SOURCE_PRESENT")
        self.assertEqual(status["atomic"]["count"],0)
        self.assertEqual(status["unified"]["status"],"SOURCE_NOT_FOUND")
        self.assertEqual(plan(self.quality,self.reviews,self.paths)["ready_count"],0)
    def test_unapproved_blocks(self):
        self.assertEqual(plan(self.quality,{},self.paths)["ready_count"],0)
    def test_stale_review_blocks(self):
        self.reviews["sense-x"]["meaning"]="changed"
        self.assertEqual(plan(self.quality,self.reviews,self.paths)["ready_count"],0)
    def test_preview_read_only(self):
        result=register(self.quality,self.reviews,self.paths,self.provenance,commit=False)
        self.assertEqual(result["ready_count"],1)
        self.assertFalse(result["production_changed"])
        self.assertEqual(Path(self.paths["atomic"]).read_text(),"")
    def test_explicit_registration_and_second_pass_block(self):
        result=register(self.quality,self.reviews,self.paths,self.provenance,commit=True)
        self.assertTrue(result["production_changed"])
        self.assertIn("光電効果",Path(self.paths["atomic"]).read_text(encoding="utf-8"))
        self.assertIn("光電効果",Path(self.paths["unified"]).read_text(encoding="utf-8"))
        audit=json.loads(self.provenance.read_text(encoding="utf-8"))
        self.assertEqual(len(audit),1)
        self.assertFalse(audit[0]["truth_verified"])
        with self.assertRaises(ValueError):
            register(self.quality,self.reviews,self.paths,self.provenance,commit=True)
    def test_existing_subject_blocks(self):
        Path(self.paths["atomic"]).write_text(json.dumps({"subject":"光電効果","value":"古い説明"},ensure_ascii=False)+"\n",encoding="utf-8")
        self.assertEqual(plan(self.quality,self.reviews,self.paths)["ready_count"],0)
    def test_missing_provenance_blocks_commit(self):
        self.provenance.unlink()
        with self.assertRaises(ValueError):
            register(self.quality,self.reviews,self.paths,self.provenance,commit=True)
    def test_unreadable_store_blocks(self):
        Path(self.paths["truth"]).write_text("not-json",encoding="utf-8")
        self.assertEqual(store_status(self.paths)["truth"]["status"],"SOURCE_UNREADABLE")

if __name__=="__main__":unittest.main()
