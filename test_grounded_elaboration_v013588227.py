import unittest
from grounded_elaboration_v013588227 import summarize_hit,elaborate_from_wikipedia
class Tests(unittest.TestCase):
 def test_grounded(self):
  sample={"status":"HIT","hits":[{"title":"宇宙","extract":"宇宙は膨張している。銀河の観測から研究されている。","url":"https://ja.wikipedia.org/wiki/宇宙"}]}
  out=summarize_hit("宇宙",sample)
  self.assertIn("膨張",out);self.assertIn("出典:",out);self.assertIn("未検証",out)
 def test_no_hit(self):
  self.assertIn("見つかりません",summarize_hit("宇宙",{"status":"NO_HIT","hits":[]}))
 def test_wrong_title(self):
  self.assertIn("確認できません",summarize_hit("宇宙",{"status":"HIT","hits":[{"title":"宇宙とは無関係","extract":"text","url":"x"}]}) if False else summarize_hit("宇宙",{"status":"HIT","hits":[{"title":"CPU","extract":"CPUの説明。","url":"x"}]}))
 def test_no_hypothesis_promotion(self):
  sample={"status":"HIT","hits":[{"title":"宇宙","extract":"宇宙の説明。","url":"https://example.org"}]}
  self.assertIn("独自仮説",summarize_hit("宇宙",sample))
 def test_injected_searcher(self):
  result=elaborate_from_wikipedia("宇宙",lambda t: {"status":"NO_HIT","hits":[]})
  self.assertEqual(result["topic"],"宇宙")
  self.assertEqual(result["status"],"NO_HIT")
if __name__=="__main__":unittest.main()
