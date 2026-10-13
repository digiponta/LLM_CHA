"""v0.4.28.14 comparison integrity and missing-label tests."""
import unittest
from compare_gate_relevance_v042814 import compare
from review_semantic_relevance_v042813 import template
class Tests(unittest.TestCase):
    def sample(self):
        validation={"records":[{"id":f"A{i:02d}","turn":1,"question":"Q","final_answer":"A",
          "gate_resolution":"ACCEPT","candidate_alignment":"SINGLE_TURN_CONFIRMED",
          "literal_probe_identity":False,"manual_review":{}} for i in range(1,65)]}
        capture={"groups":[{"id":f"A{i:02d}","turns":[{"question":"Q","response":"A",
          "gate":"[gate=KNOWN, sem_agreement=0.9, resolution=ACCEPT]"}]} for i in range(1,57)]}
        for i in range(57,65):
            capture["groups"][i-57]["turns"].append({"question":"Q","response":"A",
              "gate":"[gate=KNOWN, sem_agreement=0.9, resolution=ACCEPT]"})
        for i in range(57,65):
            validation["records"][i-1]["id"]=f"A{i-56:02d}"
            validation["records"][i-1]["turn"]=2
        reviews=[{k:("" if v is None else str(v)) for k,v in row.items()} for row in template(validation)]
        return validation,capture,reviews
    def test_no_labels_not_failure(self):
        v,c,rows=self.sample();r=compare(v,c,rows)
        self.assertEqual(r["human_relevance_labeled"],0)
        self.assertEqual(r["labeled_accept_relevance_conflicts"],0)
    def test_explicit_conflict(self):
        v,c,rows=self.sample();rows[0]["final_relevant"]="false"
        r=compare(v,c,rows)
        self.assertEqual(r["paired_score_and_human_relevance"],1)
        self.assertEqual(r["labeled_accept_relevance_conflicts"],1)
    def test_alignment_guard(self):
        v,c,rows=self.sample();c["groups"][0]["turns"][0]["response"]="wrong"
        with self.assertRaises(ValueError):compare(v,c,rows)
    def test_label_guard(self):
        v,c,rows=self.sample();rows[0]["final_relevant"]="maybe"
        with self.assertRaises(ValueError):compare(v,c,rows)
    def test_no_inferred_causality(self):
        v,c,rows=self.sample();r=compare(v,c,rows)
        self.assertFalse(r["causal_attribution_established"])
        self.assertTrue(all(x["root_cause"]=="UNDETERMINED" for x in r["records"]))
if __name__=="__main__":unittest.main()
