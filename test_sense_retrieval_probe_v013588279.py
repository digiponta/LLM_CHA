import json,tempfile,unittest
from pathlib import Path
from sense_retrieval_probe_v013588279 import probe

class RetrievalProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
        self.atomic=d/"atomic.jsonl";self.unified=d/"unified.jsonl";self.audit=d/"audit.json"
        self.atomic.write_text(json.dumps({"subject":"閃亜鉛鉱","value":"亜鉛の硫化鉱物である"},ensure_ascii=False)+"\n",encoding="utf-8")
        self.unified.write_text(json.dumps({"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は、亜鉛の硫化鉱物である。"},ensure_ascii=False)+"\n",encoding="utf-8")
        self.audit.write_text(json.dumps([{"subject":"閃亜鉛鉱","candidate_id":"sense-ab912703fcc269a1","evidence_sentence":"閃亜鉛鉱（スファレライト）は亜鉛の硫化鉱物である。"}],ensure_ascii=False),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_three_routes(self):
        x=probe(self.atomic,self.unified,self.audit)
        self.assertEqual(x["source_status"],"READY")
        self.assertEqual([a["route"] for a in x["answers"]],["ATOMIC_EXACT","EVIDENCE_ALIAS","ATTRIBUTE_NOT_EXPLICIT"])
        self.assertFalse(x["production_changed"])
    def test_missing_provenance_blocks(self):
        self.audit.write_text("[]",encoding="utf-8")
        x=probe(self.atomic,self.unified,self.audit)
        self.assertEqual(x["source_status"],"SOURCE_NOT_READY")
    def test_missing_alias_evidence_blocks_alias(self):
        self.audit.write_text(json.dumps([{"subject":"閃亜鉛鉱","candidate_id":"sense-ab912703fcc269a1","evidence_sentence":"閃亜鉛鉱は亜鉛の硫化鉱物である。"}],ensure_ascii=False),encoding="utf-8")
        x=probe(self.atomic,self.unified,self.audit)
        self.assertEqual(x["answers"][1]["route"],"UNKNOWN")
    def test_formula_not_hallucinated(self):
        x=probe(self.atomic,self.unified,self.audit)
        self.assertNotIn("ZnS",x["answers"][2]["answer"])
if __name__=="__main__":unittest.main()
