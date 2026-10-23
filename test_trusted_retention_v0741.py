import unittest
from verify_trusted_retention_v0741 import status_for_pairs,summarize

class TrustedRetentionTests(unittest.TestCase):
    def test_binding_distinguishes_checkpoint_and_state(self):
        rows=[{"id":"a","fingerprint":"x"},{"id":"b","fingerprint":"y"}]
        out=status_for_pairs(rows,{"x","y"},{"x"})
        self.assertTrue(out[0]["both_bound"])
        self.assertFalse(out[1]["both_bound"])
        self.assertTrue(out[1]["state_bound"])
        self.assertFalse(out[1]["checkpoint_bound"])
    def test_nll_summary(self):
        r=summarize([{"target_nll":2.0,"first_top1":True},
                     {"target_nll":1.0,"first_top1":False}])
        self.assertEqual(r,{"count":2,"mean_nll":1.5,"first_top1":1})
    def test_state_loader_requires_path(self):
        import json,tempfile
        from pathlib import Path
        from internalized_knowledge_v10100 import load_trained_fingerprints
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp)/"state.json"
            state.write_text(json.dumps({"trained_fingerprints":["example"]}),encoding="utf-8")
            self.assertIn("example",load_trained_fingerprints(state))
    def test_empty_summary(self):
        self.assertEqual(summarize([])["mean_nll"],None)
if __name__=="__main__":unittest.main()
