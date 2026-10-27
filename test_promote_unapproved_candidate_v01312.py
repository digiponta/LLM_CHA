import tempfile
import unittest
from pathlib import Path
from promote_unapproved_candidate_v01312 import assess

class PromotionPreflightTests(unittest.TestCase):
    def test_valid_metrics_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/x for x in ("base.pt","candidate.pt","pilot-state.json")]
            for path in paths:path.write_bytes(b"sample")
            report={"promoted":False,"pilot_count":16,
                    "pilot_fit":{"delta_nll":-0.24725},
                    "stability_retention":{"delta_nll":-0.001063},
                    "base_fingerprint_count":61,"candidate_fingerprint_count":77}
            self.assertEqual(assess(report,*paths),[])
    def test_regression_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/x for x in ("base.pt","candidate.pt","pilot-state.json")]
            for path in paths:path.write_bytes(b"x")
            report={"promoted":False,"pilot_count":16,"pilot_fit":{"delta_nll":-0.1},
                    "stability_retention":{"delta_nll":0.2},
                    "base_fingerprint_count":61,"candidate_fingerprint_count":77}
            self.assertIn("STABILITY_REGRESSION_OR_MISSING",assess(report,*paths))
    def test_missing_candidate_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/x for x in ("base.pt","candidate.pt","pilot-state.json")]
            self.assertIn("CANDIDATE_MISSING",assess({},*paths))
if __name__=="__main__":unittest.main()
