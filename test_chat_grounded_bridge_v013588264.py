import json
import tempfile
import unittest
from pathlib import Path
from chat_grounded_bridge_v013588264 import answer

def record(id_,question,title,excerpt):
 return {"id":id_,"question":question,"evidence":{"status":"EVIDENCE","topic":title,"excerpt":excerpt,"url":"https://example.invalid/"+id_},
         "source":{"title":title},"review":{"status":"PENDING_HUMAN_REVIEW"}}
class GroundedChatTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.path=Path(self.tmp.name)/"data.json"
  self.items=[
   record("s","スファレライトの化学組成は","閃亜鉛鉱","閃亜鉛鉱は亜鉛鉱物である。成分は硫化亜鉛であり、純粋なものは白色である。"),
   record("w","水の化学組成は","水","水とは、化学式 H2O で表される、水素と酸素の化合物である。"),
   record("u","宇宙とは","宇宙","英語 outer space は地球の大気圏外の空間を指し、日本語では宇宙空間と呼ぶ。")]
  self.path.write_text(json.dumps({"cases":self.items},ensure_ascii=False),encoding="utf-8")
 def tearDown(self):self.tmp.cleanup()
 def test_composition_grounded(self):
  r=answer("スファレライトの化学組成は",self.path)
  self.assertEqual(r["status"],"BOUND_EXTRACT_ACCEPTED")
  self.assertIn("硫化亜鉛",r["answer"])
  self.assertIn("未承認",r["answer"])
 def test_water(self):
  self.assertEqual(answer("水の化学組成は",self.path)["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_sense_safety(self):
  self.assertEqual(answer("宇宙とは",self.path)["status"],"ABSTAIN_SENSE_MISMATCH")
 def test_unrelated_subject(self):
  self.assertEqual(answer("銀河の化学組成は",self.path)["status"],"ABSTAIN_NO_UNIQUE_SOURCE")
 def test_missing_file(self):
  self.assertEqual(answer("水とは",self.path.with_name("missing.json"))["status"],"ABSTAIN_NO_SNAPSHOT")
 def test_no_silent_writes(self):
  before=self.path.read_bytes()
  answer("水の化学組成は",self.path)
  self.assertEqual(before,self.path.read_bytes())
if __name__=="__main__": unittest.main()
