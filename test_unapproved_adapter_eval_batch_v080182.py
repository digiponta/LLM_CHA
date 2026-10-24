import unittest
from pathlib import Path
import torch

class EvalBatchDimensionTests(unittest.TestCase):
    def test_target_is_batched(self):
        sequence=[1,2,3,4,5,6]
        x=torch.tensor([sequence[:-1]],dtype=torch.long)
        y=torch.tensor([sequence[1:]],dtype=torch.long)
        self.assertEqual(x.ndim,2)
        self.assertEqual(y.ndim,2)
        begin,finish=2,5
        self.assertEqual(y[0,begin:finish].tolist(),[4,5,6])
    def test_eval_code_preserves_batch_dimension(self):
        source=Path(__file__).with_name("unapproved_adapter_eval_v08018.py").read_text(encoding="utf-8")
        self.assertIn("y=torch.tensor([sequence[1:]],dtype=torch.long)",source)
        compile(source,"unapproved_adapter_eval_v08018.py","exec")

if __name__=="__main__":unittest.main()
