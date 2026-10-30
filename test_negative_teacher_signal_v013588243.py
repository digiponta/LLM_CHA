import json
import tempfile
import unittest
from pathlib import Path
import torch
from online_train import load_approved_negative_pairs

class NegativeTeacherTests(unittest.TestCase):
 def test_only_approved_pending_pair_eligible(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"repairs.jsonl"
   records=[
    {"question":"宇宙","answer_candidate":"宇宙は膨張している。","rejected_candidate":"無意味な出力",
     "approval":"EXPLICIT_HUMAN","state":"APPROVED","gate":"REJECT_NOT_ENTAILED"},
    {"question":"CPU","answer_candidate":"CPUは中央処理装置。","rejected_candidate":"誤回答",
     "approval":"PENDING","state":"PENDING_REVIEW","gate":"REJECT_NOT_ENTAILED"}]
   p.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in records),encoding="utf-8")
   rows=load_approved_negative_pairs(p,[("宇宙","宇宙は膨張している。","chat-manual")])
   self.assertEqual(rows,[("宇宙","宇宙は膨張している。","無意味な出力")])
 def test_no_unmatched_good(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"repairs.jsonl"
   p.write_text(json.dumps({"question":"宇宙","answer_candidate":"良い","rejected_candidate":"悪い",
       "approval":"EXPLICIT_HUMAN","state":"APPROVED","gate":"REJECT_NOT_ENTAILED"},ensure_ascii=False)+"\n",encoding="utf-8")
   self.assertEqual(load_approved_negative_pairs(p,[("宇宙","別の正解","chat-manual")]),[])
 def test_missing_file(self):
  self.assertEqual(load_approved_negative_pairs(Path("not-present-negative-repair-test.jsonl"),[]),[])
if __name__=="__main__":unittest.main()
