import tempfile
import unittest
from pathlib import Path
from negative_teacher_signal_v013588244 import append_negative_signal,make_negative_signal
class NegativeOnlyTests(unittest.TestCase):
 def test_rejected_signal_only(self):
  row=make_negative_signal("宇宙","誤った応答","REJECT_NOT_ENTAILED",{"topic":"宇宙"})
  self.assertEqual(row["signal"],"NEGATIVE")
  self.assertEqual(row["training_status"],"NOT_TRAINED")
  self.assertIsNone(row["positive_answer"])
 def test_deduplicate(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"negative.jsonl"
   a=append_negative_signal(path,"宇宙","誤回答","REJECT_NOT_ENTAILED")
   b=append_negative_signal(path,"宇宙","誤回答","REJECT_NOT_ENTAILED")
   self.assertEqual(a["status"],"RECORDED")
   self.assertEqual(b["status"],"DUPLICATE")
   self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()),1)
 def test_no_accepted_signal(self):
  with self.assertRaisesRegex(ValueError,"NOT_REJECTED"):
   make_negative_signal("宇宙","正答","ACCEPT")
 def test_empty_candidate(self):
  with self.assertRaisesRegex(ValueError,"EMPTY_NEGATIVE_SIGNAL"):
   make_negative_signal("宇宙","","REJECT_UNKNOWN")
if __name__=="__main__":unittest.main()
