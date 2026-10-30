import unittest
from evidence_aware_route_v013588236 import encode_request,decode_request,generation_prompt
class Tests(unittest.TestCase):
 def test_roundtrip(self):
  cmd=encode_request("宇宙","宇宙は膨張。\n空間が変化。")
  self.assertEqual(len(cmd.splitlines()),1)
  topic,excerpt=decode_request(cmd)
  self.assertEqual(topic,"宇宙")
  self.assertEqual(excerpt,"宇宙は膨張。 空間が変化。")
 def test_reject_malformed(self):
  with self.assertRaises(ValueError):decode_request("/evidence-candidate bad?")
 def test_bounded(self):
  topic,excerpt=decode_request(encode_request("宇宙"*1000,"資料"*1000))
  self.assertLessEqual(len(topic),100)
  self.assertLessEqual(len(excerpt),450)
 def test_prompt(self):
  self.assertIn("\nAI:",generation_prompt("宇宙","宇宙は膨張"))
 def test_regular_question_is_not_command(self):
  with self.assertRaisesRegex(ValueError,"NOT_EVIDENCE_COMMAND"):decode_request("宇宙とは")
if __name__=="__main__":unittest.main()
