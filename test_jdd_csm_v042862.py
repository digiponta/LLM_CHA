import json
import tempfile
import unittest
from pathlib import Path
from benchmark_jdd_csm_v042862 import evaluate

def sample(i):
 return {"conversation_id":f"jdd-t1-{i}","source_dialogue_id":i,
         "topic_name":"Synthetic","train_ready":False,
         "original_speakers_preserved":True,
         "turns":[{"turn_id":1,"speaker":"A","text":"私は車を持っていない"},
                  {"turn_id":2,"speaker":"B","text":"東京で映画を見ました"}]}
class JDDCSMTests(unittest.TestCase):
 def evaluate_rows(self,rows,limit=None,recent_limit=5):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"test.jsonl"
   p.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n",encoding="utf-8")
   return evaluate(p,limit,recent_limit)
 def test_counts(self):
  r=self.evaluate_rows([sample(1),sample(2)])
  self.assertEqual(r["counts"]["dialogues"],2)
  self.assertEqual(r["counts"]["utterances"],4)
 def test_keyword_baseline(self):
  r=self.evaluate_rows([sample(1)])
  self.assertGreater(r["counts"]["keyword_hits"],0)
 def test_no_propositions(self):
  r=self.evaluate_rows([sample(1)])
  self.assertFalse(r["speaker_aware_proposition_extraction"])
 def test_no_cross_session(self):
  r=self.evaluate_rows([sample(1),sample(2)])
  self.assertFalse(r["cross_conversation_memory_merging"])
 def test_no_training(self):
  self.assertFalse(self.evaluate_rows([sample(1)])["train_ready"])
 def test_duplicate_session_rejected(self):
  with self.assertRaises(ValueError):self.evaluate_rows([sample(1),sample(1)])
 def test_invalid_speaker_rejected(self):
  d=sample(1);d["turns"][0]["speaker"]="user"
  with self.assertRaises(ValueError):self.evaluate_rows([d])
 def test_nonsequential_turn_rejected(self):
  d=sample(1);d["turns"][1]["turn_id"]=3
  with self.assertRaises(ValueError):self.evaluate_rows([d])
 def test_limit(self):
  self.assertEqual(self.evaluate_rows([sample(1),sample(2)],limit=1)["counts"]["dialogues"],1)
 def test_recent_window(self):
  a=self.evaluate_rows([sample(1)],recent_limit=1)
  b=self.evaluate_rows([sample(1)],recent_limit=2)
  self.assertLess(a["counts"]["recent_context_chars"],b["counts"]["recent_context_chars"])
if __name__=="__main__":unittest.main()
