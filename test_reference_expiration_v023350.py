import unittest
from reference_expiration_v023350 import evaluate
class ReferenceExpirationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.results=evaluate()
    def test_six_diagnostics(self):
        self.assertEqual(self.results["total"],6)
        self.assertEqual({x["id"] for x in self.results["cases"]},
                         {"valid_before_ttl","expired_after_ttl","replayed_yes",
                          "cross_context","switch_invalidation","turn_limit"})
    def test_safety(self):
        failures=[x for x in self.results["cases"] if not x["passed"]]
        self.assertEqual(failures,[],f"Failed expiry diagnostics: {failures}")
if __name__=="__main__":unittest.main()
