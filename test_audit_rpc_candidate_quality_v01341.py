import unittest
from audit_rpc_candidate_quality_v01341 import prepare,analyze,validate_labels,qualified

class CandidateAuditTests(unittest.TestCase):
    def fixture(self):
        return {"details":[{"dialogue_id":"d1","prompt":"相手: 猫","selected_index":1,
                            "candidates":[{"index":0,"text":"猫ですね"},{"index":1,"text":"はい"}]},
                           {"dialogue_id":"d2","prompt":"相手: 犬","selected_index":0,
                            "candidates":[{"index":0,"text":"犬"},{"index":1,"text":"そう"}]}]}
    def filled(self,items):
        for item in items:
            item["reviewer"]="reviewer1"
            item["scores"]={k:3 for k in item["scores"]}
        return items
    def test_deterministic_blind(self):
        x,m=prepare(self.fixture(),13)
        y,_=prepare(self.fixture(),13)
        self.assertEqual(x,y)
        self.assertEqual(len(m),4)
        self.assertTrue(all("reference" not in str(row) and "rank_score" not in str(row) for row in x))
    def test_reject_pending(self):
        items,m=prepare(self.fixture())
        with self.assertRaises(ValueError):validate_labels(items,m)
    def test_completed_all_valid(self):
        items,m=prepare(self.fixture());self.filled(items)
        out=analyze(self.fixture(),items,m)
        self.assertEqual(out["human_oracle_cases"],2)
        self.assertEqual(out["selected_qualified_cases"],2)
    def test_reject_partial(self):
        items,m=prepare(self.fixture());self.filled(items)
        with self.assertRaises(ValueError):validate_labels(items[:-1],m)
    def test_quality_threshold(self):
        self.assertFalse(qualified({"context_fit":3,"japanese_fluency":3,"topic_continuity":1,"question_response":3}))
        self.assertTrue(qualified({"context_fit":2,"japanese_fluency":2,"topic_continuity":2,"question_response":2}))

if __name__=="__main__":unittest.main()
