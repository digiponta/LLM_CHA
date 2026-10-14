import copy
import unittest
from review_precision_v042845 import DIMENSIONS, evaluate, sample, wilson

def audit(n=12):
    return {"version":"v0.4.28.44","mode":"CONTEXT_QA_HEURISTIC_AUDIT",
            "accepted":0,"train_ready":False,"audited_context":n,
            "source_sha256":"fixture", "audit_records":[
                {"id":f"id{i}","source_line":i+1,"question":f"Q{i}?",
                 "answer":f"A{i}","audit_status":"review_priority_normal",
                 "flags":[],"review_status":"pending","train_eligible":False}
                for i in range(n)]}

class ReviewPrecisionTests(unittest.TestCase):
    def test_sample_size(self):
        self.assertEqual(len(sample(audit(), 5)["records"]), 5)

    def test_reproducible_order_independent(self):
        a = audit()
        b = copy.deepcopy(a)
        b["audit_records"].reverse()
        ids = lambda x: [r["id"] for r in x["records"]]
        self.assertEqual(ids(sample(a, 6)), ids(sample(b, 6)))

    def test_template_never_approved(self):
        s = sample(audit(), 4)
        self.assertFalse(s["train_ready"])
        self.assertTrue(all(r["review_status"] == "pending" for r in s["records"]))

    def test_pending_has_no_precision(self):
        r = evaluate(sample(audit(), 4))
        self.assertIsNone(r["observed_precision"])
        self.assertEqual(r["unresolved"], 4)

    def test_all_pass(self):
        s = sample(audit(), 5)
        for r in s["records"]:
            r["ratings"] = {k: "pass" for k in DIMENSIONS}
        e = evaluate(s)
        self.assertEqual(e["observed_precision"], 1.0)
        self.assertLess(e["wilson_95_ci"][0], 1.0)
        self.assertFalse(e["train_ready"])

    def test_failure_and_unknown(self):
        s = sample(audit(), 3)
        s["records"][0]["ratings"] = {k:"pass" for k in DIMENSIONS}
        s["records"][1]["ratings"] = {k:"fail" for k in DIMENSIONS}
        s["records"][2]["ratings"] = {k:"unknown" for k in DIMENSIONS}
        e = evaluate(s)
        self.assertEqual((e["fully_adjudicated"],e["all_dimensions_pass"],e["unresolved"]), (2,1,1))
        self.assertEqual(e["observed_precision"], .5)
        self.assertFalse(e["precision_estimable_without_missingness_bias"])

    def test_reject_duplicate_ids(self):
        s = sample(audit(), 2)
        s["records"][1]["id"] = s["records"][0]["id"]
        with self.assertRaises(ValueError):
            evaluate(s)

    def test_reject_unsafe_audit(self):
        a = audit()
        a["audit_records"][0]["review_status"] = "approved"
        with self.assertRaises(ValueError):
            sample(a, 5)

    def test_wilson_empty(self):
        self.assertIsNone(wilson(0, 0))

    def test_reject_oversample(self):
        with self.assertRaises(ValueError):
            sample(audit(3), 5)

if __name__ == "__main__":
    unittest.main()
