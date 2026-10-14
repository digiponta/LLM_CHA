import json
import tempfile
import unittest
from pathlib import Path
from prepare_japanese_daily_dialogue_v042861 import normalize,convert_directory,split_for

def example(i=1,topic="Travel"):
 return {"topic_id":3,"topic_name":topic,"dialogue_id":i,"dialogue_length":3,
  "utterances":[{"turn_num":1,"speaker":"A","utterance":"合成会話A"},
                {"turn_num":2,"speaker":"B","utterance":"合成会話B"},
                {"turn_num":3,"speaker":"A","utterance":"合成会話C"}]}

class JapaneseDailyDialogueTests(unittest.TestCase):
 def test_id(self):
  self.assertEqual(normalize(example(),"synthetic.json",42861)["conversation_id"],"jdd-t3-1")
 def test_speakers(self):
  self.assertEqual([t["speaker"] for t in normalize(example(),"synthetic.json",42861)["turns"]],["A","B","A"])
 def test_source_order(self):
  self.assertEqual([t["turn_id"] for t in normalize(example(),"synthetic.json",42861)["turns"]],[1,2,3])
 def test_stable_split(self):
  self.assertEqual(split_for("jdd-t3-1"),split_for("jdd-t3-1"))
 def test_bad_turn_number(self):
  d=example();d["utterances"][1]["turn_num"]=3
  with self.assertRaises(ValueError):normalize(d,"synthetic.json",42861)
 def test_declared_length(self):
  d=example();d["dialogue_length"]=4
  with self.assertRaises(ValueError):normalize(d,"synthetic.json",42861)
 def test_duplicate_rejected(self):
  with tempfile.TemporaryDirectory() as root:
   src=Path(root)/"source";src.mkdir()
   (src/"synthetic.json").write_text(json.dumps([example(),example()],ensure_ascii=False),encoding="utf-8")
   with self.assertRaises(ValueError):convert_directory(src,Path(root)/"output")
 def test_local_export(self):
  with tempfile.TemporaryDirectory() as root:
   src=Path(root)/"source";src.mkdir()
   (src/"synthetic.json").write_text(json.dumps([example(1),example(2)],ensure_ascii=False),encoding="utf-8")
   out=Path(root)/"output"
   r=convert_directory(src,out)
   self.assertEqual(r["dialogue_count"],2)
   self.assertEqual(r["utterance_count"],6)
   self.assertFalse(r["train_ready"])
   self.assertEqual(sum(1 for k in ("train","val","test") for line in (out/f"jdd_{k}_v042861.jsonl").read_text(encoding="utf-8").splitlines()),2)
 def test_no_chatbot_ready(self):
  row=normalize(example(),"synthetic.json",42861)
  self.assertFalse(row["train_ready"])
  self.assertFalse(row["synthetic_linking"])
 def test_invalid_speaker(self):
  d=example();d["utterances"][0]["speaker"]="user"
  with self.assertRaises(ValueError):normalize(d,"synthetic.json",42861)
if __name__=="__main__":unittest.main()
