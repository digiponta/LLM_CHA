import unittest
from temporary_evidence_v01358824 import TemporaryEvidence
from causal_evidence_retrieval_v01358829 import retrieve_cause
class CausalTests(unittest.TestCase):
 def create(self,text):
  s=TemporaryEvidence();s.set_topic("スファレライト");s.add(text,"clipboard");return s
 def test_explicit(self):
  s=self.create("スファレライト\n硬度が低く特定方向に割れやすいため、カットが難しい。")
  self.assertEqual(retrieve_cause(s,"なぜカットが難しい？")["status"],"SUPPORTED_EXCERPT")
 def test_hardness_alone_not_cause(self):
  s=self.create("スファレライト\nモース硬度：3.5～4")
  self.assertEqual(retrieve_cause(s,"なぜカットが難しい？")["status"],"NO_CAUSAL_EVIDENCE")
 def test_no_topic(self):
  self.assertEqual(retrieve_cause(TemporaryEvidence(),"なぜカットが難しい？")["status"],"NO_TOPIC")
 def test_question_guard(self):
  self.assertIsNone(retrieve_cause(self.create("スファレライト"),"屈折率は？"))
 def test_other_topic(self):
  s=self.create("スファレライト\n硬度が低いためカットが難しい。")
  s.set_topic("スターバックス")
  self.assertEqual(retrieve_cause(s,"なぜカットが難しい？")["status"],"NO_EVIDENCE")
 def test_no_hallucination(self):
  s=self.create("スファレライト\nダイヤモンドのカットが難しいため")
  self.assertEqual(retrieve_cause(s,"なぜカットが難しい？")["status"],"NO_CAUSAL_EVIDENCE")
if __name__=="__main__":unittest.main()
