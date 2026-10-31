"""Explicit-subject normal chat routing tests: no GPU / network required."""
import json
import tempfile
import unittest
from pathlib import Path
from chat_unified_grounding_v013588265 import classify_auto,route

def item(id_,title,excerpt):
    return {"id":id_,"question":title,"source":{"title":title},
            "evidence":{"status":"EVIDENCE","topic":title,"excerpt":excerpt,
                        "url":"https://example.invalid/"+id_},
            "review":{"status":"PENDING_HUMAN_REVIEW"}}

class UnifiedGroundingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"snapshot.json"
        self.data={"cases":[
          item("s","閃亜鉛鉱","閃亜鉛鉱は亜鉛の鉱物である。成分は硫化亜鉛であり純粋なものは白色である。"),
          item("w","水","水とは、化学式 H2O で表される水素と酸素の化合物である。"),
          item("u","宇宙","英語 outer space は、地球の大気圏外の空間を指し、日本語では宇宙空間と呼ぶことが一般的である。")]}
        self.path.write_text(json.dumps(self.data,ensure_ascii=False),encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_sphalerite_normal_question(self):
        result=route("スファレライトの化学組成は",self.path)
        self.assertEqual(result["status"],"BOUND_EXTRACT_ACCEPTED")
        self.assertIn("硫化亜鉛",result["answer"])
    def test_water_normal_question(self):
        self.assertEqual(route("水の化学組成は",self.path)["status"],"BOUND_EXTRACT_ACCEPTED")
    def test_sense_mismatch_abstains(self):
        self.assertEqual(route("宇宙とは",self.path)["status"],"BOUND_SENSE_NOTICE")
    def test_no_ungrounded_fallback_when_sense_mismatch(self):
        self.assertIsNotNone(route("宇宙とは",self.path))
    def test_unrelated_subject_uses_old_route(self):
        self.assertIsNone(route("銀河の化学組成は",self.path))
    def test_social_chat_uses_old_route(self):
        self.assertIsNone(route("宝石としてスファレライトが好きです",self.path))
    def test_commands_unaffected(self):
        self.assertFalse(classify_auto("/grounded 水の化学組成は"))
        self.assertFalse(classify_auto("/good"))
    def test_missing_snapshot_uses_old_route(self):
        self.assertIsNone(route("水の化学組成は",self.path.with_name("missing.json")))
    def test_does_not_write(self):
        original=self.path.read_bytes()
        route("水の化学組成は",self.path)
        self.assertEqual(original,self.path.read_bytes())
if __name__=="__main__":unittest.main()
