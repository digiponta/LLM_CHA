import unittest
from pathlib import Path
import torch
import torch.nn.functional as F

class AdapterEvalShapeTests(unittest.TestCase):
    def test_contiguous_target_span(self):
        logits=torch.randn(1,8,12)
        prefix=[1,2,3]
        target=[4,5,6]
        sequence=prefix+target
        y=torch.tensor([sequence[1:]],dtype=torch.long)
        begin=len(prefix)-1
        finish=begin+len(target)
        selected=logits[0,begin:finish,:]
        gold=y[0,begin:finish]
        self.assertEqual(tuple(selected.shape),(3,12))
        self.assertEqual(tuple(gold.shape),(3,))
        self.assertEqual(tuple(torch.softmax(selected,-1).gather(1,gold[:,None]).shape),(3,1))
        self.assertTrue(torch.isfinite(F.cross_entropy(selected,gold)))
    def test_syntax_and_shape_checks(self):
        source=Path(__file__).with_name("unapproved_adapter_eval_v08018.py").read_text(encoding="utf-8")
        compile(source,"unapproved_adapter_eval_v08018.py","exec")
        self.assertIn("expected [batch, time, vocab] logits",source)
        self.assertIn("target/logit shape mismatch",source)
if __name__=="__main__":unittest.main()
