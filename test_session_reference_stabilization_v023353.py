import unittest
from session_reference_stabilization_v023353 import evaluate

class SessionReferenceStabilizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=evaluate()

    def test_all_runtime_scenarios(self):
        self.assertEqual(self.report["total"],13)
        failures=[c for c in self.report["cases"] if not c["passed"]]
        self.assertEqual(failures,[],f"Runtime failures: {failures}")

    def test_restart_and_expiry(self):
        indexed={c["id"]:c for c in self.report["cases"]}
        for name in ("restart_approved_reuse","pending_not_autoapproved_on_restart",
                     "expiration_boundary","invalidation_persists"):
            with self.subTest(name=name):
                self.assertTrue(indexed[name]["passed"])

    def test_no_unapproved_writes(self):
        indexed={c["id"]:c for c in self.report["cases"]}
        for name in ("stale_pending_id_rejected","cancel_and_delayed_yes",
                     "ambiguous_yes_no_approval","switch_does_not_approve"):
            with self.subTest(name=name):
                self.assertTrue(indexed[name]["passed"])

if __name__=="__main__":
    unittest.main()
