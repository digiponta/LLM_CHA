import json
import tempfile
import unittest
from pathlib import Path
from evaluate_semantic_generation_v0100 import score,load_cases

class GenerationTests(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(score("宇宙は膨張する。","宇宙は膨張する")["exact"])
    def test_different(self):
        self.assertFalse(score("別の答え","宇宙は膨張する")["exact"])
    def test_empty_not_correct(self):
        self.assertFalse(score("","")["exact"])
    def test_supplied_holdout_unattested(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"holdout.json"
            file.write_text(json.dumps([{"concept":"宇宙","question":"宇宙って何","answer":"宇宙"}],ensure_ascii=False),encoding="utf-8")
            records,source=load_cases("",file)
            self.assertEqual(len(records),1)
            self.assertEqual(source,"USER_SUPPLIED_HOLDOUT_UNATTESTED")
if __name__=="__main__":unittest.main()
