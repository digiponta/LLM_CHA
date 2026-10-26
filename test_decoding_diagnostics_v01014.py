import unittest
from decoding_diagnostics_v01014 import normalize, repeated_fragment, audit

def row(i, guess, reference, cap=False):
    return {"id":str(i),"category":"both_incorrect","baseline_output":guess,
            "challenger_output":guess,"reference":reference,
            "baseline_cap_hit":cap,"challenger_cap_hit":cap}

class TestDiagnostics(unittest.TestCase):
    def test_nfkc(self):
        self.assertEqual(normalize("解読／分析"), normalize("解読/分析"))
    def test_unicode_only(self):
        result=audit({"protocol":"TRAIN_ASSOCIATED_DEV_NOT_HOLDOUT",
                      "records":[row(1,"解読/分析","解読／分析")]})
        self.assertEqual(result["summary"]["beam3_exact"],0)
        self.assertEqual(result["summary"]["beam3_normalized_exact"],1)
    def test_termination_not_invented(self):
        result=audit({"protocol":"TRAIN_ASSOCIATED_DEV_NOT_HOLDOUT",
                      "records":[row(1,"foo","bar")]})
        self.assertEqual(result["records"][0]["beam3_termination"],"STOP_REASON_UNOBSERVED")
    def test_cap(self):
        result=audit({"protocol":"TRAIN_ASSOCIATED_DEV_NOT_HOLDOUT",
                      "records":[row(1,"foo","bar",True)]})
        self.assertEqual(result["records"][0]["beam3_termination"],"TOKEN_CAP_REACHED")
    def test_repetition(self):
        self.assertTrue(repeated_fragment("空気、空気、空気、空気"))
        self.assertFalse(repeated_fragment("物質波はドブロイ波である。"))
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            audit({"protocol":"TRAIN_ASSOCIATED_DEV_NOT_HOLDOUT","records":[]})

if __name__=="__main__":
    unittest.main()
