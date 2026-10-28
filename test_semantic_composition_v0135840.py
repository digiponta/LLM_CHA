import unittest
from semantic_composition_v0135840 import answer,DEFAULT_PROBES,assess
class Tests(unittest.TestCase):
 def test_expected_routes(self):
  for ident,q,expected in DEFAULT_PROBES:
   with self.subTest(ident=ident):self.assertTrue(assess(expected,answer(q)))
 def test_composition(self):
  r=answer("『吾輩は猫である』の著者と語り手を教えて。")
  self.assertIn("夏目漱石",r["answer"])
  self.assertIn("名前のない猫",r["answer"])
  self.assertEqual(len(r["sources"]),2)
 def test_unknown_abstain(self):
  self.assertEqual(answer("作者は誰？")["status"],"ABSTAIN")
 def test_yesno(self):
  self.assertIn("はい",answer("『吾輩は猫である』を書いたのは漱石ですか？")["answer"])
if __name__=="__main__":unittest.main()
