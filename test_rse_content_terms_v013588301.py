import unittest
from rse_content_terms_v013588301 import keywords,index,search
class M:
 def __init__(self,s):self.s=s
 def dictionary_form(self):return self.s
 def part_of_speech(self):return ("名詞","","","","","")
class T:
 def tokenize(self,s):return [M(x) for x in s.split()]
class Tests(unittest.TestCase):
 def test_generic_only_abstains(self):
  self.assertEqual(search([], "どう 今",T())["reason"],"NO_CONTENT_TERMS")
 def test_specific_topic_no_match(self):
  rows=index([{"user":"猫 名前","assistant":"タマ"}],T())
  x=search(rows,"スファレライト とは",T())
  self.assertEqual(x["status"],"ABSTAIN")
 def test_matching_topic_selected_for_review_only(self):
  rows=index([{"user":"猫 名前","assistant":"タマ"}],T())
  x=search(rows,"猫 名前",T())
  self.assertEqual(x["status"],"SELECTED_REVIEW_REQUIRED")
  self.assertNotIn("answer",str(x))
 def test_requires_all_terms(self):
  rows=index([{"user":"猫 名前","assistant":"タマ"}],T())
  self.assertEqual(search(rows,"猫 飼育",T())["status"],"ABSTAIN")
if __name__=="__main__":unittest.main()
