import unittest
from diagnose_offline_generation_v0135813 import divergence,REFERENCES

class OfflineDiagnosticsTests(unittest.TestCase):
    def test_five_reference_probes(self):
        self.assertEqual(len(REFERENCES),5)
        self.assertEqual(len({x["id"] for x in REFERENCES}),5)
    def test_identical_tokens(self):
        result=divergence({"base":[1,2,3],"A":[1,2,3]})
        self.assertTrue(result["A"]["identical"])
        self.assertIsNone(result["A"]["first_difference_index"])
    def test_first_token_divergence(self):
        result=divergence({"base":[1,2,3],"B":[9,2,3]})
        self.assertEqual(result["B"]["matched_prefix_tokens"],0)
        self.assertEqual(result["B"]["first_difference_index"],0)
    def test_different_length(self):
        result=divergence({"base":[1,2,3],"C":[1,2]})
        self.assertEqual(result["C"]["first_difference_index"],2)
    def test_no_automatic_ranking(self):
        self.assertEqual({x["id"] for x in REFERENCES},
                         {"persona","explanation","casual","followup","literature"})
if __name__=="__main__":unittest.main()
