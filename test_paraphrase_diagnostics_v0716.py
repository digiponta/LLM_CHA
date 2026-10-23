import unittest
from diagnose_paraphrase_v0716 import diagnose

def case(question,reference,output):
    return {"question":question,"reference":reference,
            "outputs":{"experimental":output}}

class ParaphraseDiagnosticsTests(unittest.TestCase):
    def test_exact_and_wrong_fact(self):
        r=diagnose({"version":"v0.7.15","holdout_cases":[
            case("blue","AO-17","AO-17"),
            case("red","RB-42","AO-17"),
            case("green","GC-83","GC-83です。"),
            case("white","WB-26","無関係です。")]})
        self.assertEqual(r["class_counts"]["exact"],1)
        self.assertEqual(r["class_counts"]["cross_fact_confusion"],1)
        self.assertEqual(r["class_counts"]["contains_reference_but_not_exact"],1)
        self.assertEqual(r["class_counts"]["other"],1)
    def test_empty_response(self):
        r=diagnose({"holdout_cases":[case("x","AO-17","")]})
        self.assertEqual(r["class_counts"]["empty"],1)
    def test_unrecognized_reference(self):
        with self.assertRaises(ValueError):
            diagnose({"holdout_cases":[case("x","NOT-A-CODE","foo")]})
    def test_diagnostics_does_not_claim_verification(self):
        r=diagnose({"holdout_cases":[]})
        self.assertEqual(r["cases"],0)
        self.assertIn("no factual validation",r["note"])
if __name__=="__main__":unittest.main()
