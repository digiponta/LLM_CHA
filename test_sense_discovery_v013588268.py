import unittest
from evidence_sense_discovery_v013588268 import discover,inspect_snapshot

def evidence(txt,topic="光電効果"):
    return {"status":"EVIDENCE","topic":topic,"excerpt":txt,"url":"https://example.invalid/entry"}

class DiscoveryTests(unittest.TestCase):
    sentence="光電効果とは、物質に光を照射すると電子が放出される現象である。"
    def test_find_definition(self):
        x=discover(evidence(self.sentence))
        self.assertEqual(len(x),1)
        self.assertEqual(x[0]["subject"],"光電効果")
        self.assertFalse(x[0]["approved"])
    def test_subject_boundary_to_wa(self):
        x=discover(evidence("光電効果とは、電子が放出される現象である。"))
        self.assertEqual(x[0]["subject"],"光電効果")
        self.assertNotEqual(x[0]["subject"],"光電効果と")

    def test_repeatable_identity(self):
        self.assertEqual(discover(evidence(self.sentence))[0]["id"],discover(evidence(self.sentence))[0]["id"])
    def test_duplicate(self):
        x=discover(evidence(self.sentence))[0]
        y=discover(evidence(self.sentence),[x])[0]
        self.assertEqual(y["review_status"],"POSSIBLE_DUPLICATE")
    def test_conflict(self):
        y=discover(evidence(self.sentence),[{"id":"other","subject":"光電効果","meaning":"別の現象である"}])[0]
        self.assertEqual(y["review_status"],"POSSIBLE_CONFLICT")
    def test_history_rejected(self):
        self.assertEqual(discover(evidence("光電効果とは、かつて別の力学の現象であると考えられていた。")),[])
    def test_subject_mismatch(self):
        self.assertEqual(discover(evidence(self.sentence,topic="電気")),[])
    def test_missing_evidence(self):
        self.assertEqual(discover({"status":"NO_EVIDENCE","topic":"光電効果","excerpt":self.sentence}),[])
    def test_diagnostic_no_approval(self):
        x=inspect_snapshot({"cases":[{"id":"x","evidence":evidence(self.sentence)}]})
        self.assertEqual(x["candidate_count"],1)
        self.assertEqual(x["approved_count"],0)
        self.assertFalse(x["production_changed"])

if __name__=="__main__":unittest.main()
