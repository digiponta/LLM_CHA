import unittest
from compare_labeled_qa_v042822 import compare
from review_semantic_relevance_v042813 import template
class Tests(unittest.TestCase):
    def fixture(self):
        v={"records":[{"id":f"T{i:02d}","turn":1,"question":"量子力学とは","final_answer":"量子力学について",
        "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
        "literal_probe_identity":False,"manual_review":{}} for i in range(64)]}
        rows=[{k:("" if val is None else str(val)) for k,val in r.items()} for r in template(v)]
        return v,rows
    def test_zero_labels(self):
        v,r=self.fixture();s=compare(v,r)
        self.assertFalse(s["between_class_comparison_available"])
        self.assertIsNone(s["difference_in_means"])
    def test_one_class_only(self):
        v,r=self.fixture();r[0]["final_relevant"]="true"
        self.assertFalse(compare(v,r)["between_class_comparison_available"])
    def test_two_classes(self):
        v,r=self.fixture();r[0]["final_relevant"]="true";r[1]["final_relevant"]="false"
        s=compare(v,r)
        self.assertTrue(s["between_class_comparison_available"])
        self.assertEqual(s["lexical_statistics"]["positive"]["n"],1)
        self.assertEqual(s["lexical_statistics"]["negative"]["n"],1)
    def test_unknown_labels_rejected(self):
        v,r=self.fixture();r[0]["final_relevant"]="unknown"
        with self.assertRaises(ValueError):compare(v,r)
    def test_read_only(self):
        v,r=self.fixture();s=compare(v,r)
        self.assertFalse(s["runtime_modified"])
        self.assertFalse(s["threshold_estimated"])
        self.assertEqual(s["classifier_accuracy"],"NOT_MEASURED")
if __name__=="__main__":unittest.main()
