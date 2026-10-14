import json
import tempfile
import unittest
from pathlib import Path
from diagnose_jdd_extraction_v042864 import diagnose

def case(text,topic="Dailylife",cid="jdd-t1-1"):
 return {"conversation_id":cid,"topic_name":topic,"train_ready":False,
 "original_speakers_preserved":True,
 "turns":[{"turn_id":1,"speaker":"A","text":text},
          {"turn_id":2,"speaker":"B","text":"こんにちは"}]}
class DiagnoseTests(unittest.TestCase):
 def run_cases(self,items):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup)
  p=Path(td.name)/"synthetic.jsonl"
  p.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in items)+"\n",encoding="utf-8")
  return diagnose(p,per_topic=10)
 def test_total_counts(self):
  x=self.run_cases([case("車はありますか")]);self.assertEqual(x["totals"]["utterances"],2)
 def test_question(self):
  x=self.run_cases([case("車はありますか？")]);self.assertEqual(x["totals"]["feature_question"],1)
 def test_first_person_unmatched(self):
  x=self.run_cases([case("私は電車で移動する")]);self.assertEqual(x["totals"]["unmatched_explicit_first_person"],1)
 def test_matched_proposition(self):
  x=self.run_cases([case("私は車を持っていない")]);self.assertEqual(x["totals"]["matched_utterances"],1)
 def test_no_raw_text(self):
  x=self.run_cases([case("私は電車で移動する")]);self.assertNotIn("私は電車で移動する",json.dumps(x,ensure_ascii=False))
 def test_topic(self):
  x=self.run_cases([case("こんにちは",topic="Travel")]);self.assertEqual(x["sampled_by_topic"]["Travel"],1)
 def test_no_gold_claims(self):
  x=self.run_cases([case("こんにちは")]);self.assertIsNone(x["extraction_precision"]);self.assertIsNone(x["extraction_recall"])
 def test_no_training(self):
  x=self.run_cases([case("こんにちは")]);self.assertFalse(x["train_ready"])
 def test_overlap(self):
  x=self.run_cases([case("私は車を持っていませんか？")]);self.assertTrue(x["heuristic_categories_can_overlap"])
 def test_duplicate_rejected(self):
  d=case("こんにちは")
  with self.assertRaises(ValueError):self.run_cases([d,d])
if __name__=="__main__":unittest.main()
