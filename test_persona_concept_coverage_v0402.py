import tempfile
import unittest
from pathlib import Path
from persona_concept_coverage_v0402 import inspect

class PersonaConceptCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"corpus.txt"
        self.path.write_text("数学は世界を記述する。\n文学では物語を語る。\n私は数学を使って問題を解く。",encoding="utf-8")
    def tearDown(self):self.temp.cleanup()
    def test_evidence_for_existing(self):
        rows=inspect(self.path,("数学",))["concepts"]
        self.assertTrue(rows[0]["raw_evidence_present"])
        self.assertTrue(rows[0]["ranked_persona_available"])
    def test_missing_concept(self):
        row=inspect(self.path,("小説",))["concepts"][0]
        self.assertFalse(row["raw_evidence_present"])
        self.assertFalse(row["ranked_persona_available"])
    def test_coverage_independent_of_means(self):
        row=inspect(self.path,("文学",))["concepts"][0]
        self.assertTrue(row["raw_evidence_present"])
        self.assertEqual(row["means_role_candidate_count"],0)
    def test_means_report(self):
        row=inspect(self.path,("数学",))["concepts"][0]
        self.assertEqual(row["means_role_candidate_count"],1)
    def test_no_runtime_claim(self):
        d=inspect(self.path)
        self.assertFalse(d["runtime_route_measured"])
        self.assertTrue(all(r["runtime_route"]=="NOT_PROBED" for r in d["concepts"]))
    def test_no_corpus_write(self):
        old=self.path.read_bytes()
        inspect(self.path)
        self.assertEqual(old,self.path.read_bytes())
    def test_default_four_concepts(self):
        self.assertEqual([x["concept"] for x in inspect(self.path)["concepts"]],
                         ["数学","量子力学","文学","小説"])
    def test_evidence_source_provenance(self):
        x=inspect(self.path,("数学",))["concepts"][0]
        self.assertGreaterEqual(x["ranked_selected"][0]["line"],1)
        self.assertEqual(x["ranked_selected"][0]["factual_truth"],"NOT_ASSESSED")
if __name__=="__main__":unittest.main()
