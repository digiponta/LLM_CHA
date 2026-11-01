import unittest
from evaluate_rse_shadow_v013588310 import evaluate
class RSEShadowTests(unittest.TestCase):
 def setUp(self):
  self.items=[{"id":"a","dialogue_id":"1","question":"こんばんはー。","answer":"こんばんは！"}]
  self.h={"split":"test","cases":[{"id":"a","dialogue_id":"1","question_chars":7,"answer_chars":6}]}
  self.review={"source_split":"test","cases":[{"id":"a","dialogue_id":"1","new_query":"こんばんは","intent_match":True,"slot_match":True,"answer_suitable":True,"persona_transfer_risk":False}]}
 def test_shadow_no_auto_response(self):
  x=evaluate(self.h,self.review,self.items)
  self.assertFalse(x["live_auto_accept_enabled"])
  self.assertEqual(x["cases"],1)
  self.assertNotIn("source_answer",str(x))
  self.assertEqual(x["labels_source"],"AI_PROVISIONAL_NOT_HUMAN_VERIFIED")
 def test_incomplete_fails(self):
  self.review["cases"][0]["answer_suitable"]=None
  with self.assertRaises(ValueError):evaluate(self.h,self.review,self.items)
 def test_source_tamper_fails(self):
  self.items[0]["answer"]="改変"
  with self.assertRaises(ValueError):evaluate(self.h,self.review,self.items)
 def test_equal_query_fails(self):
  self.review["cases"][0]["new_query"]="こんばんはー。"
  with self.assertRaises(ValueError):evaluate(self.h,self.review,self.items)
 def test_split_fails(self):
  self.review["source_split"]="train"
  with self.assertRaises(ValueError):evaluate(self.h,self.review,self.items)
if __name__=="__main__":unittest.main()
