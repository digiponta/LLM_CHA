import json,tempfile,unittest
from pathlib import Path
from chat_semantic_retrieval_v013588280 import classify,route

class ParaphraseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        d=self.root/"data";d.mkdir()
        (d/"semantic_propositions_v1090.jsonl").write_text(json.dumps({"subject":"閃亜鉛鉱","value":"亜鉛の硫化鉱物である"},ensure_ascii=False)+"\n",encoding="utf-8")
        (d/"unified_semantic_memory_v1090.jsonl").write_text(json.dumps({"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は、亜鉛の硫化鉱物である。"},ensure_ascii=False)+"\n",encoding="utf-8")
        (d/"sense_registration_provenance_v013588273.json").write_text(json.dumps([{"subject":"閃亜鉛鉱","candidate_id":"sense-ab912703fcc269a1","evidence_sentence":"閃亜鉛鉱（スファレライト）は亜鉛の硫化鉱物である。"}],ensure_ascii=False),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_subject_paraphrase(self):
        self.assertEqual(route("閃亜鉛鉱について教えて",self.root)["route"],"MEMORY_ATOMIC_EXACT")
    def test_alias_paraphrase(self):
        self.assertEqual(route("スファレライトって何？",self.root)["route"],"MEMORY_EVIDENCE_ALIAS")
    def test_formula_paraphrase(self):
        x=route("スファレライトの化学式は？",self.root)
        self.assertEqual(x["route"],"MEMORY_ATTRIBUTE_NOT_EXPLICIT")
        self.assertNotIn("ZnS",x["answer"])
    def test_unrelated_not_intercepted(self):
        self.assertIsNone(route("今日は何をしてる？",self.root))
        self.assertIsNone(route("閃亜鉛鉱の産地は？",self.root))
    def test_bare_alias(self):
        self.assertEqual(classify("スファレライト"),("スファレライトとは？","MEMORY_EVIDENCE_ALIAS"))
    def test_original_questions_still_supported(self):
        for q in ("閃亜鉛鉱とは？","スファレライトとは？","閃亜鉛鉱の化学組成は？"):
            self.assertIsNotNone(route(q,self.root))
    def test_missing_alias_evidence_abstains(self):
        f=self.root/"data/sense_registration_provenance_v013588273.json"
        f.write_text(json.dumps([{"subject":"閃亜鉛鉱","candidate_id":"sense-ab912703fcc269a1","evidence_sentence":"閃亜鉛鉱は鉱物である。"}],ensure_ascii=False),encoding="utf-8")
        self.assertEqual(route("スファレライトって何？",self.root)["route"],"MEMORY_EVIDENCE_NOT_READY")
if __name__=="__main__":unittest.main()
