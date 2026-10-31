import json,tempfile,unittest
from pathlib import Path
from chat_semantic_retrieval_v013588280 import route

class RuntimeRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        d=self.root/"data";d.mkdir()
        (d/"semantic_propositions_v1090.jsonl").write_text(json.dumps({"subject":"閃亜鉛鉱","value":"亜鉛の硫化鉱物である"},ensure_ascii=False)+"\n",encoding="utf-8")
        (d/"unified_semantic_memory_v1090.jsonl").write_text(json.dumps({"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は、亜鉛の硫化鉱物である。"},ensure_ascii=False)+"\n",encoding="utf-8")
        (d/"sense_registration_provenance_v013588273.json").write_text(json.dumps([{"subject":"閃亜鉛鉱","candidate_id":"sense-ab912703fcc269a1","evidence_sentence":"閃亜鉛鉱（スファレライト）は亜鉛の硫化鉱物である。"}],ensure_ascii=False),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_exact(self):
        self.assertEqual(route("閃亜鉛鉱とは？",self.root)["route"],"MEMORY_ATOMIC_EXACT")
    def test_alias(self):
        self.assertEqual(route("スファレライトとは？",self.root)["route"],"MEMORY_EVIDENCE_ALIAS")
    def test_formula_abstain(self):
        x=route("閃亜鉛鉱の化学組成は？",self.root)
        self.assertEqual(x["route"],"MEMORY_ATTRIBUTE_NOT_EXPLICIT")
        self.assertNotIn("ZnS",x["answer"])
    def test_other_chat_not_intercepted(self):
        self.assertIsNone(route("元気？",self.root))
    def test_missing_store_fails_closed(self):
        (self.root/"data/semantic_propositions_v1090.jsonl").unlink()
        self.assertEqual(route("閃亜鉛鉱とは？",self.root)["route"],"MEMORY_SOURCE_NOT_FOUND")

if __name__=="__main__":unittest.main()
