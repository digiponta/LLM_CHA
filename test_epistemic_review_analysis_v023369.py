import hashlib,tempfile,unittest
from pathlib import Path
from epistemic_calibration_v023368 import dataset
from epistemic_review_analysis_v023369 import validate_review,error_analysis

class ReviewAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"corpus.txt"
        self.path.write_text("量子力学では可能性を扱う。\n量子力学は映像のようなもの。\n",encoding="utf8")
        self.data=dataset(self.path,"量子力学")
    def test_unreviewed_no_metrics(self):
        rows=validate_review(self.data,self.path)
        self.assertIsNone(error_analysis(rows)["metrics"])
    def test_one_reviewed_label_metrics(self):
        self.data["rows"][0].update(review_status="REVIEWED",gold_labels=["CONTEXT_ONLY"])
        report=error_analysis(validate_review(self.data,self.path))
        self.assertEqual(report["reviewed_count"],1)
        self.assertEqual(report["by_label"]["CONTEXT_ONLY"]["candidate_labels"]["tp"],1)
    def test_source_change_rejected(self):
        self.path.write_text("量子力学は別の記述。",encoding="utf8")
        with self.assertRaises(ValueError):validate_review(self.data,self.path)
    def test_context_tamper_rejected(self):
        self.data["rows"][0]["context"]="書き換え"
        with self.assertRaises(ValueError):validate_review(self.data,self.path)
    def test_offset_tamper_rejected(self):
        self.data["rows"][0]["mention_start"]+=1
        with self.assertRaises(ValueError):validate_review(self.data,self.path)
    def test_unreviewed_with_gold_rejected(self):
        self.data["rows"][0]["gold_labels"]=["OPINION"]
        with self.assertRaises(ValueError):validate_review(self.data,self.path)
    def test_reviewed_without_gold_rejected(self):
        self.data["rows"][0]["review_status"]="REVIEWED"
        with self.assertRaises(ValueError):validate_review(self.data,self.path)
    def test_invalid_gold_rejected(self):
        self.data["rows"][0].update(review_status="REVIEWED",gold_labels=["TRUE"])
        with self.assertRaises(ValueError):validate_review(self.data,self.path)
    def test_overlapping_gold_and_disagreement(self):
        self.data["rows"][1].update(review_status="REVIEWED",gold_labels=["ANALOGY","OPINION"])
        report=error_analysis(validate_review(self.data,self.path))
        self.assertEqual(report["reviewed_count"],1)
        self.assertGreater(len(report["disagreements"]),0)
    def test_read_only_corpus(self):
        original=self.path.read_bytes()
        validate_review(self.data,self.path)
        self.assertEqual(self.path.read_bytes(),original)

if __name__=="__main__": unittest.main()
