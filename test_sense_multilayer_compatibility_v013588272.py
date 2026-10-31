import unittest
from sense_multilayer_compatibility_v013588272 import inspect
def cand():
    return {"id":"sense-x","subject":"光電効果","meaning":"電子を放出する現象である","quality_gate":"PASS"}
class MultilayerTests(unittest.TestCase):
    def test_all_empty(self):
        r=inspect([cand()],{})
        self.assertEqual(r["case_count"],1)
        self.assertEqual(r["rows"][0]["layers"]["truth"],"NO_TRUTH_RECORD")
        self.assertEqual(r["rows"][0]["layers"]["atomic"],"NO_MATCHING_SUBJECT")
    def test_cross_layer_hits(self):
        r=inspect([cand()],{"atomic":[{"subject":"光電効果","value":"電子を放出する現象である"}],
            "subject_index":[{"subject":"光電効果","value":"電子を放出する現象である"}],
            "typed_index":[{"subject":"光電効果","value":"別の説明"}],
            "unified":[{"subject":"光電効果","value":"電子を放出する現象である"}]})
        layers=r["rows"][0]["layers"]
        self.assertEqual(layers["atomic"],"EXACT_VALUE_MATCH")
        self.assertEqual(layers["subject_index"],"EXACT_VALUE_MATCH")
        self.assertEqual(layers["typed_index"],"REVIEW_SENSE_OR_CONFLICT")
        self.assertEqual(layers["unified"],"EXACT_VALUE_MATCH")
    def test_truth_block(self):
        r=inspect([cand()],{"truth":[{"subject":"光電効果","state":"REJECTED"}]})
        self.assertTrue(r["rows"][0]["truth_blocked"])
    def test_no_approval(self):
        r=inspect([cand()],{})
        self.assertFalse(r["production_changed"])
        self.assertEqual(r["approved_count"],0)
        self.assertTrue(r["rows"][0]["manual_review_required"])
if __name__=="__main__":unittest.main()
