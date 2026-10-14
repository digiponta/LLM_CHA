import json
import tempfile
import unittest
from pathlib import Path
from benchmark_jdd_speaker_aware_v042863 import speaker_extract,balanced_rows,benchmark,TOPICS

def dialogue(i,topic):
 return {"conversation_id":f"jdd-t{i}-{i}","topic_name":topic,
         "train_ready":False,"original_speakers_preserved":True,
         "turns":[{"turn_id":1,"speaker":"A","text":"私は車を持っていない"},
                  {"turn_id":2,"speaker":"B","text":"私は映画が好きです"}]}

class SpeakerAwareTests(unittest.TestCase):
 def path(self,rows):
  tmp=tempfile.TemporaryDirectory()
  self.addCleanup(tmp.cleanup)
  p=Path(tmp.name)/"synthetic.jsonl"
  p.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n",encoding="utf-8")
  return p
 def test_a_owns(self):
  p=speaker_extract("s",{"turn_id":1,"speaker":"A","text":"私は車を持っていない"})
  self.assertEqual((p[0]["subject"],p[0]["polarity"]),("A",False))
 def test_b_likes(self):
  p=speaker_extract("s",{"turn_id":2,"speaker":"B","text":"私は映画が好きです"})
  self.assertEqual((p[0]["subject"],p[0]["predicate"]),("B","likes"))
 def test_no_user_assignment(self):
  p=speaker_extract("s",{"turn_id":1,"speaker":"A","text":"私は車を持っています"})
  self.assertNotEqual(p[0]["subject"],"user")
 def test_provenance(self):
  p=speaker_extract("s",{"turn_id":4,"speaker":"B","text":"私は車を持っています"})
  self.assertEqual((p[0]["conversation_id"],p[0]["source_turn"]),("s",4))
 def test_unmatched(self):
  self.assertEqual(speaker_extract("s",{"turn_id":1,"speaker":"A","text":"おはよう"}),[])
 def test_speaker_reject(self):
  with self.assertRaises(ValueError):speaker_extract("s",{"turn_id":1,"speaker":"user","text":"私は車を持っている"})
 def test_balanced(self):
  p=self.path([dialogue(i+1,topic) for i,topic in enumerate(TOPICS)])
  r=benchmark(p,per_topic=1)
  self.assertEqual(r["counts"]["dialogues"],5)
  self.assertEqual(set(r["sampled_by_topic"]),set(TOPICS))
 def test_counts(self):
  p=self.path([dialogue(1,"Dailylife")])
  r=benchmark(p,per_topic=1)
  self.assertEqual(r["counts"]["candidate_propositions"],2)
 def test_stable(self):
  p=self.path([dialogue(i+1,topic) for i,topic in enumerate(TOPICS)])
  a,_=balanced_rows(p,1);b,_=balanced_rows(p,1)
  self.assertEqual([x["conversation_id"] for x in a],[x["conversation_id"] for x in b])
 def test_duplicate_session(self):
  d=dialogue(1,"Dailylife")
  with self.assertRaises(ValueError):balanced_rows(self.path([d,d]),1)
 def test_no_training(self):
  r=benchmark(self.path([dialogue(1,"Dailylife")]),1)
  self.assertFalse(r["train_ready"])
  self.assertIsNone(r["precision"])
if __name__=="__main__":unittest.main()
