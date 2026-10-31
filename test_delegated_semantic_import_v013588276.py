import json,tempfile,unittest
from pathlib import Path
from delegated_semantic_import_v013588276 import inspect,register,AUTHORIZATION,ALLOWED_ID

def fixture(root):
    paths={k:str(root/(k+".jsonl")) for k in ("atomic","subject_index","typed_index","unified","truth")}
    for p in paths.values():Path(p).write_text("",encoding="utf-8")
    c={"id":ALLOWED_ID,"subject":"閃亜鉛鉱","meaning":"亜鉛の硫化鉱物である",
       "quality_gate":"PASS","review_status":"PENDING_HUMAN_REVIEW",
       "source_trust":"EXTERNAL_UNVERIFIED","source_url":"https://ja.wikipedia.org/wiki/閃亜鉛鉱",
       "evidence_sentence":"閃亜鉛鉱は、亜鉛の硫化鉱物である。"}
    q={"candidates":[c],"id_migrations":[{"id":ALLOWED_ID,"new_id":ALLOWED_ID,"review_transfer_allowed":False}]}
    a={"records":[{**c,"candidate_id":ALLOWED_ID,"decision":"RECOMMEND_APPROVE",
                   "reviewer_type":"AI_DELEGATE","human_review_recorded":False,"note":"Definition checked"}]}
    audit=root/"audit.json";audit.write_text("[]",encoding="utf-8")
    return paths,q,a,audit

class DelegatedGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.p,self.q,self.a,self.audit=fixture(Path(self.tmp.name))
    def tearDown(self):self.tmp.cleanup()
    def test_authorization_required(self):
        self.assertFalse(inspect(self.q,self.a,self.p,self.audit,"")["ready"])
    def test_preview_read_only(self):
        r=register(self.q,self.a,self.p,self.audit,AUTHORIZATION)
        self.assertTrue(r["ready"])
        self.assertFalse(r["production_changed"])
    def test_missing_store_blocks(self):
        Path(self.p["truth"]).unlink()
        self.assertFalse(inspect(self.q,self.a,self.p,self.audit,AUTHORIZATION)["ready"])
    def test_stale_evidence_blocks(self):
        self.a["records"][0]["meaning"]="changed"
        self.assertFalse(inspect(self.q,self.a,self.p,self.audit,AUTHORIZATION)["ready"])
    def test_defer_blocks(self):
        self.a["records"][0]["decision"]="DEFER"
        self.assertFalse(inspect(self.q,self.a,self.p,self.audit,AUTHORIZATION)["ready"])
    def test_existing_unified_subject_blocks(self):
        Path(self.p["unified"]).write_text(json.dumps({"concept":"閃亜鉛鉱","assistant":"既存説明"},ensure_ascii=False)+"\n",encoding="utf-8")
        self.assertFalse(inspect(self.q,self.a,self.p,self.audit,AUTHORIZATION)["ready"])
    def test_commit_and_audit(self):
        r=register(self.q,self.a,self.p,self.audit,AUTHORIZATION,commit=True)
        self.assertTrue(r["production_changed"])
        a=json.loads(self.audit.read_text(encoding="utf-8"))
        self.assertFalse(a[0]["human_approved"])
        self.assertTrue(a[0]["delegated_approved"])
        self.assertIn("閃亜鉛鉱",Path(self.p["unified"]).read_text(encoding="utf-8"))
        self.assertFalse(inspect(self.q,self.a,self.p,self.audit,AUTHORIZATION)["ready"])

if __name__=="__main__":unittest.main()
