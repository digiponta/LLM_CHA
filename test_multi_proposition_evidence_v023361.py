import unittest
from multi_proposition_evidence_v023361 import evaluate,validate,Evidence

class MultiPropositionTests(unittest.TestCase):
    def test_all_scenarios(self):
        report=evaluate()
        self.assertEqual(report["total"],11)
        self.assertEqual(report["passed"],11,
            [x for x in report["cases"] if not x["passed"]])
    def test_explicit_chain_provenance(self):
        r=validate([Evidence("AはBを含む","TRUE","fixture","edge-a"),
                    Evidence("BはCを含む","TRUE","fixture","edge-b")],
                   "AはCを含む",transitive_relations=frozenset({"includes"}))
        self.assertEqual(r["status"],"supported")
        self.assertEqual(r["path"],["edge-a","edge-b"])
    def test_no_unapproved_transitivity(self):
        r=validate([Evidence("AはBを含む","TRUE","fixture","e1"),
                    Evidence("BはCを含む","TRUE","fixture","e2")],
                   "AはCを含む")
        self.assertEqual(r["status"],"blocked")
    def test_cycles_terminate(self):
        r=validate([Evidence("AはBを含む","TRUE","fixture","e1"),
                    Evidence("BはAを含む","TRUE","fixture","e2")],
                   "AはCを含む",transitive_relations=frozenset({"includes"}))
        self.assertEqual(r["status"],"blocked")
if __name__=="__main__":
    unittest.main()
