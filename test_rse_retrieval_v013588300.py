import unittest
from rse_retrieval_v013588300 import build,select,retrieve
class RSETests(unittest.TestCase):
 def setUp(self):
  self.docs=build([{"user":"猫の名前は","assistant":"タマです"},{"user":"今日は晴れ","assistant":"いい天気ですね"},{"user":"最近どう","assistant":"元気です"}])
 def test_exact_retrieval(self):
  x=select(self.docs,"猫の名前は")
  self.assertEqual(x["answer"],"タマです")
  self.assertFalse(x["expanded"])
 def test_abstain_no_overlap(self):
  x=select(self.docs,"quantum zzz")
  self.assertEqual(x["status"],"ABSTAIN")
 def test_no_answer_content_ranking(self):
  self.assertEqual(retrieve(self.docs,"タマです"),[])
 def test_unverified_selection(self):
  self.assertFalse(select(self.docs,"最近どう")["semantic_relevance_verified"])
if __name__=="__main__":unittest.main()
