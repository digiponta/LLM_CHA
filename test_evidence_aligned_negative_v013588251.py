import json
import tempfile
import unittest
from pathlib import Path
from evidence_aligned_negative_v013588251 import capture_negative,load_aligned
from train_evidence_aligned_negative_v013588251 import encode_aligned

class FakeTokenizer:
 def encode(self,text,add_bos=False,add_eos=False):
  values=[ord(c)%50+2 for c in text]
  return ([1] if add_bos else [])+values+([0] if add_eos else [])

class EvidenceAlignedNegativeTests(unittest.TestCase):
 def test_capture_exact_prompt(self):
  ev={"status":"EVIDENCE","topic":"宇宙","excerpt":"宇宙膨張を示す資料。","url":"https://example.test"}
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/"signals.jsonl"
   self.assertEqual(capture_negative(path,ev,"1967年 APB","REJECT_NOT_ENTAILED"),"RECORDED")
   self.assertEqual(capture_negative(path,ev,"1967年 APB","REJECT_NOT_ENTAILED"),"DUPLICATE")
   rows=load_aligned(path)
   self.assertEqual(len(rows),1)
   self.assertEqual(rows[0]["prompt"],"人: 宇宙を説明してください。参考文: 宇宙膨張を示す資料。\nAI:")
   self.assertEqual(rows[0]["training_status"],"NOT_TRAINED")
 def test_reject_nonnegative_gate(self):
  with tempfile.TemporaryDirectory() as folder:
   with self.assertRaises(ValueError):
    capture_negative(Path(folder)/"s.jsonl",{"status":"EVIDENCE","topic":"宇宙","excerpt":"資料"},"正解","ACCEPT")
 def test_answer_positions_keep_evidence_context(self):
  p="人: 宇宙について。参考文: 証拠\nAI:"
  xs,ys=encode_aligned(FakeTokenizer(),p,"否定",32)
  self.assertGreater(len(xs),0)
  self.assertEqual(len(xs),len(ys))
  self.assertEqual(xs[0][-1],FakeTokenizer().encode(p)[-1])
if __name__=="__main__":unittest.main()
