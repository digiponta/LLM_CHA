import tempfile
import unittest
from pathlib import Path
from corpus_evidence_interference_v013588238 import find_corpus_context,variants,assess
class Tests(unittest.TestCase):
 def test_separate_conditions(self):
  v=variants("宇宙","膨張する","脳と宇宙")
  self.assertEqual(len(v),4)
  self.assertNotIn("脳",v["B_wikipedia"])
  self.assertNotIn("膨張",v["C_corpus"])
 def test_assessment_is_non_authoritative(self):
  r=assess({"A":"脳"}, "宇宙膨張", "脳と宇宙")
  self.assertTrue(r["A"]["requires_human_semantic_review"])
  self.assertTrue(r["A"]["mentions_brain"])
 def test_corpus_selection(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"sample.txt"
   p.write_text("脳に関する話\n宇宙について\n脳と宇宙の関係\n",encoding="utf-8")
   matches=find_corpus_context(p)
   self.assertEqual(matches[0]["line"],3)
 def test_no_match(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"sample.txt";p.write_text("数学",encoding="utf-8")
   self.assertEqual(find_corpus_context(p),[])
if __name__=="__main__":unittest.main()
