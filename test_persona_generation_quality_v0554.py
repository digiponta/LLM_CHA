import unittest
from diagnose_persona_generation_v0554 import diagnose,analyze

def sample(reply,user="今日は散歩した"):
 return {"scenario":"x","turn":1,"user":user,"raw_llm":{"reply":reply}}
class QualityTests(unittest.TestCase):
 def test_fragment(self):self.assertTrue(diagnose("の前身。","入力")["fragment_flag"])
 def test_empty(self):self.assertTrue(diagnose("","入力")["fragment_flag"])
 def test_repeated(self):self.assertTrue(diagnose("宇宙全体として、宇宙全体として、宇宙全体として。","入力")["repeated_phrase_flag"])
 def test_numeric(self):self.assertTrue(diagnose("24、24、24、24、24、24、24","入力")["numerical_loop_flag"])
 def test_no_inferred_truth(self):
  a=analyze({"rows":[sample("今日は散歩したんですね。")]})
  self.assertIsNone(a["semantic_correctness"]);self.assertIsNone(a["topic_relevance_accuracy"])
 def test_denominator(self):
  a=analyze({"rows":[sample("の前身。"),sample("今日はよく歩きましたね。")]})
  self.assertEqual(a["samples"],2);self.assertEqual(a["flag_rates"]["fragment_flag"],0.5)
 def test_empty_data(self):self.assertIsNone(analyze({"rows":[]})["bigram_overlap_mean"])
 def test_overlap(self):
  x=diagnose("今日は散歩した","今日は散歩した")
  self.assertEqual(x["input_bigram_recall_proxy"],1.0)
 def test_unrelated_overlap(self):
  x=diagnose("宇宙の話題です。","今日は散歩した")
  self.assertLess(x["input_bigram_recall_proxy"],1.0)
 def test_no_training(self):self.assertFalse(analyze({"rows":[sample("意味不明の文字列。")]})["training_recommended_automatically"])
if __name__=="__main__":unittest.main()
