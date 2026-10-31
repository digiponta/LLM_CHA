import json,tempfile,unittest
from pathlib import Path
from batch_semantic_approval_v013588277 import manifest,approve,commit

def setup(d):
    paths={k:str(d/(k+".jsonl")) for k in ("atomic","subject_index","typed_index","unified","truth")}
    for path in paths.values():Path(path).write_text("",encoding="utf-8")
    audit=d/"audit.json";audit.write_text("[]",encoding="utf-8")
    def c(id,subject):
        return {"id":id,"subject":subject,"meaning":"鉱物である",
        "quality_gate":"PASS","review_status":"PENDING_HUMAN_REVIEW",
        "evidence_sentence":subject+"は鉱物である。","source_url":"https://example.org",
        "source_trust":"EXTERNAL_UNVERIFIED"}
    a=c("s-a","閃亜鉛鉱"); b=c("s-b","保留語")
    q={"candidates":[a,b]}
    reviews={"records":[{**a,"candidate_id":"s-a","decision":"RECOMMEND_APPROVE","reviewer_type":"AI_DELEGATE",
              "human_review_recorded":False,"note":"definition reviewed"},
                       {**b,"candidate_id":"s-b","decision":"DEFER","reviewer_type":"AI_DELEGATE",
              "human_review_recorded":False,"note":"needs review"}]}
    return paths,audit,q,reviews

class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.p,self.audit,self.q,self.a=setup(Path(self.tmp.name))
    def tearDown(self):self.tmp.cleanup()
    def test_prepare_only_clear_candidate(self):
        m=manifest(self.q,self.a,self.p,self.audit)
        self.assertEqual(m["eligible_count"],1)
        self.assertEqual(m["blocked_count"],1)
        self.assertEqual(m["eligible"][0]["subject"],"閃亜鉛鉱")
        self.assertFalse(m["production_changed"])
    def test_no_does_not_commit(self):
        m=manifest(self.q,self.a,self.p,self.audit)
        with self.assertRaises(ValueError):
            commit(m,approve(m,"no"),self.q,self.a,self.p,self.audit)
        self.assertEqual(Path(self.p["atomic"]).read_text(),"")
    def test_yes_is_explicit(self):
        m=manifest(self.q,self.a,self.p,self.audit)
        self.assertEqual(approve(m,"yes")["status"],"BATCH_APPROVED")
        with self.assertRaises(ValueError):approve(m,"y")
    def test_changed_candidate_blocks(self):
        m=manifest(self.q,self.a,self.p,self.audit)
        a=approve(m,"yes")
        self.q["candidates"][0]["meaning"]="changed"
        with self.assertRaises(ValueError):
            commit(m,a,self.q,self.a,self.p,self.audit)
    def test_changed_unified_blocks(self):
        m=manifest(self.q,self.a,self.p,self.audit)
        a=approve(m,"yes")
        Path(self.p["unified"]).write_text('{"concept":"他の知識","assistant":"追加知識"}\n',encoding="utf-8")
        with self.assertRaises(ValueError):
            commit(m,a,self.q,self.a,self.p,self.audit)
    def test_store_missing_blocks(self):
        Path(self.p["truth"]).unlink()
        self.assertEqual(manifest(self.q,self.a,self.p,self.audit)["status"],"BLOCKED")
    def test_yes_commit_and_double_block(self):
        m=manifest(self.q,self.a,self.p,self.audit)
        a=approve(m,"yes")
        result=commit(m,a,self.q,self.a,self.p,self.audit)
        self.assertTrue(result["production_changed"])
        self.assertEqual(result["registered_count"],1)
        self.assertIn("閃亜鉛鉱",Path(self.p["atomic"]).read_text(encoding="utf-8"))
        self.assertIn("閃亜鉛鉱",Path(self.p["subject_index"]).read_text(encoding="utf-8"))
        self.assertIn("閃亜鉛鉱",Path(self.p["typed_index"]).read_text(encoding="utf-8"))
        self.assertIn("閃亜鉛鉱",Path(self.p["unified"]).read_text(encoding="utf-8"))
        self.assertTrue(json.loads(self.audit.read_text(encoding="utf-8"))[0]["human_batch_approved"])
        with self.assertRaises(ValueError):
            commit(m,a,self.q,self.a,self.p,self.audit)
if __name__=="__main__":unittest.main()
