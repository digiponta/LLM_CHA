import unittest
from evaluate_persona_ablation_v0552 import study

CASES=[{"id":"article","persona":"nagato","turns":[
 {"user":"今日は、量子コンピュータの記事を読んだ"},
 {"user":"量子ビットについて書かれていた","expected_topic":"量子コンピュータ"},
 {"user":"量子ビットとは？"}]}]
class AblationTests(unittest.TestCase):
 def setUp(self):self.report=study(CASES,lambda prompt:"RAW:"+prompt[-9:])
 def test_count(self):self.assertEqual(self.report["samples"],3)
 def test_real_raw_injected(self):self.assertTrue(self.report["rows"][0]["raw_llm"]["reply"].startswith("RAW:"))
 def test_controller_selected(self):self.assertEqual(self.report["rows"][0]["hybrid"]["selected"],"CONTROLLER")
 def test_followup_selected(self):self.assertEqual(self.report["rows"][1]["hybrid"]["selected"],"CONTROLLER")
 def test_question_raw(self):self.assertEqual(self.report["rows"][2]["hybrid"]["selected"],"RAW_LLM")
 def test_topic_denominator(self):self.assertEqual(self.report["topic_required"],1)
 def test_topic_numerator(self):self.assertEqual(self.report["controller_topic_retention"],1.0)
 def test_no_auto_score(self):self.assertIsNone(self.report["model_persona_consistency"])
 def test_no_learning(self):self.assertFalse(self.report["train_ready"])
 def test_bad_generator(self):
  with self.assertRaises(TypeError):study(CASES,lambda p:None)
if __name__=="__main__":unittest.main()
