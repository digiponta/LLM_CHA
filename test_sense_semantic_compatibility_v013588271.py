import unittest
from sense_semantic_compatibility_v013588271 import compare,inspect

def candidate(meaning,subject="光電効果",quality="PASS"):
    return {"id":"sense-test","subject":subject,"meaning":meaning,"quality_gate":quality}
class CompatibilityTests(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(compare(candidate("電子を放出する現象である"),[{"subject":"光電効果","value":"電子を放出する現象である"}])["status"],"EXACT_VALUE_MATCH")
    def test_normalized(self):
        self.assertEqual(compare(candidate("電子を放出する現象である。"),[{"subject":"光電効果","value":"電子を放出する現象である"}])["status"],"EXACT_VALUE_MATCH")
    def test_elaboration(self):
        self.assertEqual(compare(candidate("光を照射すると電子を放出する現象である"),[{"subject":"光電効果","value":"電子を放出する現象である"}])["status"],"POSSIBLE_ELABORATION")
    def test_unmatched(self):
        self.assertEqual(compare(candidate("電子を放出する現象である"),[])["status"],"NO_MATCHING_SUBJECT")
    def test_not_conflict_just_because_words_differ(self):
        x=compare(candidate("光に関する現象である"),[{"subject":"光電効果","value":"電子の運動に関する現象である"}])
        self.assertEqual(x["status"],"REVIEW_SENSE_OR_CONFLICT")
    def test_block_unqualified(self):
        self.assertEqual(compare(candidate("説明である",quality="PENDING"),[])["status"],"BLOCKED_UNQUALIFIED")
    def test_no_auto_approval(self):
        x=inspect([candidate("現象である")],[])
        self.assertEqual(x["approved_count"],0)
        self.assertFalse(x["production_changed"])
        self.assertTrue(x["rows"][0]["manual_review_required"])

if __name__=="__main__":
    unittest.main()
