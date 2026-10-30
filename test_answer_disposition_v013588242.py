import unittest
from answer_disposition_v013588242 import answer_disposition

class AnswerDispositionTests(unittest.TestCase):
 def test_rejection(self):
  self.assertIn("破棄",answer_disposition("EVIDENCE_GATE","REJECT_NOT_ENTAILED"))
 def test_accepted(self):
  self.assertIn("採用",answer_disposition("EVIDENCE_GATE","ACCEPT_EVIDENCE"))
  self.assertNotIn("破棄",answer_disposition("EVIDENCE_GATE","ACCEPT_EVIDENCE"))
 def test_unknown_fallback(self):
  self.assertIn("採用せず",answer_disposition("UNKNOWN_FALLBACK"))
 def test_source_without_model(self):
  self.assertIn("LLM生成：なし",answer_disposition("WIKI_RETRIEVAL"))
 def test_cli_does_not_assume_generation(self):
  self.assertIn("採否未判定",answer_disposition("CLI_ANSWER"))
 def test_invalid_route(self):
  with self.assertRaises(ValueError):answer_disposition("INVALID")
if __name__=="__main__":unittest.main()
