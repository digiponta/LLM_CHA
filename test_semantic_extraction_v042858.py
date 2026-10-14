import unittest
from conversation_semantic_memory_v042857 import new_memory
from semantic_extraction_v042858 import extract_candidates,apply_turn,build_from_turns

class SemanticExtractionTests(unittest.TestCase):
 def test_car_negative(self):
  x=extract_candidates("私は車を持っていない","user",1)
  self.assertEqual(len(x),1);self.assertFalse(x[0]["polarity"])
 def test_car_positive(self):
  x=extract_candidates("私は車を持っています","user",1)
  self.assertEqual(len(x),1);self.assertTrue(x[0]["polarity"])
 def test_movie_positive(self):
  x=extract_candidates("私は映画が好きです","user",1)
  self.assertEqual(len(x),1);self.assertTrue(x[0]["polarity"])
 def test_movie_negative(self):
  x=extract_candidates("私は映画が好きじゃない","user",1)
  self.assertEqual(len(x),1);self.assertFalse(x[0]["polarity"])
 def test_assistant_not_personal(self):
  self.assertEqual(extract_candidates("私は車を持っていない","assistant",1),[])
 def test_source_span(self):
  t="こんにちは。私は車を持っていない"
  p=extract_candidates(t,"user",2)[0]
  self.assertIn("車",t[slice(*p["source_span"])])
 def test_memory_not_promoted(self):
  s=new_memory("s");apply_turn(s,"user","私は車を持っていない")
  self.assertFalse(s["train_ready"])
  self.assertEqual(s["propositions"][0]["status"],"candidate")
 def test_no_duplicates_from_previous_extractor(self):
  s=new_memory("s");apply_turn(s,"user","私は車を持っていない")
  self.assertEqual(len(s["propositions"]),1)
 def test_turn_order(self):
  s=new_memory("s")
  with self.assertRaises(ValueError):apply_turn(s,"user","私は車を持っていない",turn_id=2)
  self.assertEqual(s["last_turn"],0)
 def test_multi_turn(self):
  s=build_from_turns("s",[{"role":"user","text":"私は映画が好きです"},
       {"role":"assistant","text":"そうなんですね"}])
  self.assertEqual(s["last_turn"],2)
  self.assertEqual(len(s["propositions"]),1)
 def test_unsupported_unknown(self):
  self.assertEqual(extract_candidates("今日はカレーを食べました","user",1),[])
 def test_car_positive_plain(self):
  x=extract_candidates("私は車を持っている","user",1)
  self.assertEqual(len(x),1);self.assertTrue(x[0]["polarity"])
 def test_car_negative_polite(self):
  x=extract_candidates("私は車を持っていません","user",1)
  self.assertEqual(len(x),1);self.assertFalse(x[0]["polarity"])
 def test_car_positive_polite(self):
  x=extract_candidates("私は車を持っています","user",1)
  self.assertEqual(len(x),1);self.assertTrue(x[0]["polarity"])
if __name__=="__main__":unittest.main()
