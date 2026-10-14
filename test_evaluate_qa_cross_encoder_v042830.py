import unittest
from evaluate_qa_cross_encoder_v042830 import split_cases

class Tests(unittest.TestCase):
    def fixture(self):
        return [{"id":f"X{i:02d}","turn":1,"question":f"質問{i//2}",
          "answer":"適切" if i%2 else "不適切",
          "provisional_chatgpt_label":bool(i%2)} for i in range(64)]
    def test_groups_disjoint(self):
        train,test=split_cases(self.fixture())
        self.assertTrue({x["question"] for x in train}.isdisjoint({x["question"] for x in test}))
    def test_deterministic(self):
        self.assertEqual(split_cases(self.fixture()),split_cases(self.fixture()))
    def test_all_labeled_accounted(self):
        train,test=split_cases(self.fixture())
        self.assertEqual(len(train)+len(test),64)
    def test_unlabeled_excluded(self):
        data=self.fixture();data[0]["provisional_chatgpt_label"]=None
        train,test=split_cases(data)
        self.assertEqual(len(train)+len(test),63)
    def test_smoke_checkpoint(self):
        try:import torch
        except ImportError:self.skipTest("PyTorch absent")
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from evaluate_qa_cross_encoder_v042830 import run
        with TemporaryDirectory() as directory:
            r=run({"cases":self.fixture()},Path(directory)/"model.pt",epochs=1)
            self.assertTrue(r["checkpoint_verified"])
            self.assertFalse(r["independent_external_holdout"])
            self.assertEqual(len(r["records"]),64)
            self.assertTrue(all(x["decision"]=="ABSTAIN" for x in r["records"]))
if __name__=="__main__":unittest.main()
