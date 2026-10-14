import json
import tempfile
import unittest
from pathlib import Path
from diagnose_jdd_candidate_expansion_v042865 import expanded_candidates,benchmark

def t(text,speaker="A"):
 return {"turn_id":1,"speaker":speaker,"text":text}

class ExpansionTests(unittest.TestCase):
 def test_preference_positive(self):
  p,g=expanded_candidates("c",t("私は音楽が好き"))
  self.assertEqual((p[0]["predicate"],p[0]["polarity"]),("likes",True))
 def test_preference_negative(self):
  p,g=expanded_candidates("c",t("私は映画が嫌い"))
  self.assertFalse(p[0]["polarity"])
 def test_possession(self):
  p,g=expanded_candidates("c",t("僕は自転車を持っていません"))
  self.assertEqual((p[0]["object"],p[0]["polarity"]),("bicycle",False))
 def test_speaker_scope(self):
  p,g=expanded_candidates("c",t("私は京都に行った","B"))
  self.assertEqual(p[0]["subject"],"B")
 def test_question_abstains(self):
  p,g=expanded_candidates("c",t("私は映画が好きですか？"))
  self.assertEqual(p,[]);self.assertIn("question",g)
 def test_quotation_abstains(self):
  p,g=expanded_candidates("c",t("「私は音楽が好き」"))
  self.assertEqual(p,[]);self.assertIn("quotation",g)
 def test_reported_abstains(self):
  p,g=expanded_candidates("c",t("私は映画が好きだそうです"))
  self.assertEqual(p,[]);self.assertIn("hearsay",g)
 def test_conditional_abstains(self):
  p,g=expanded_candidates("c",t("もし私は映画が好きだったら"))
  self.assertEqual(p,[]);self.assertIn("conditional",g)
 def test_no_inferred_subject(self):
  p,g=expanded_candidates("c",t("映画が好きです"))
  self.assertEqual(p,[])
 def test_aggregates_no_text(self):
  d={"conversation_id":"jdd-t1-2","topic_name":"Dailylife","train_ready":False,
     "original_speakers_preserved":True,
     "turns":[{"turn_id":1,"speaker":"A","text":"私は音楽が好き"},
              {"turn_id":2,"speaker":"B","text":"そうですね"}]}
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/"synthetic.jsonl"
   f.write_text(json.dumps(d,ensure_ascii=False)+"\n",encoding="utf-8")
   r=benchmark(f,per_topic=1)
  self.assertEqual(r["counts"]["expanded_candidates"],1)
  self.assertNotIn("私は音楽が好き",json.dumps(r,ensure_ascii=False))
  self.assertFalse(r["train_ready"])
if __name__=="__main__":unittest.main()
