import unittest
from review_sense_candidates_v013588269 import record_decision,stage

def sample(status="PENDING_HUMAN_REVIEW"):
    return {"candidates":[{"id":"sense-abc","subject":"光電効果",
        "meaning":"電子が放出される現象である","evidence_sentence":"光電効果とは電子が放出される現象である。",
        "source_url":"https://example.invalid","source_case_id":"wiki-1",
        "review_status":status}]}

class ReviewTests(unittest.TestCase):
    def test_no_implicit_approval(self):
        self.assertEqual(stage(sample(),{})["count"],0)
    def test_requires_human_identity(self):
        with self.assertRaises(ValueError):
            record_decision(sample(),"sense-abc","APPROVE","","確認した")
    def test_requires_review_note(self):
        with self.assertRaises(ValueError):
            record_decision(sample(),"sense-abc","APPROVE","reviewer","")
    def test_unknown_id_rejected(self):
        with self.assertRaises(ValueError):
            record_decision(sample(),"not-a-candidate","APPROVE","reviewer","reviewed")
    def test_explicit_review_stages(self):
        data=sample()
        reviews=record_decision(data,"sense-abc","APPROVE","reviewer","source checked")
        staged=stage(data,reviews)
        self.assertEqual(staged["count"],1)
        self.assertFalse(staged["live_memory_changed"])
        self.assertFalse(staged["entries"][0]["external_truth_verified"])
    def test_reject_does_not_stage(self):
        data=sample()
        reviews=record_decision(data,"sense-abc","REJECT","reviewer","bad sense")
        self.assertEqual(stage(data,reviews)["count"],0)
    def test_defer_does_not_stage(self):
        data=sample()
        reviews=record_decision(data,"sense-abc","DEFER","reviewer","needs review")
        self.assertEqual(stage(data,reviews)["count"],0)
    def test_conflict_blocks_approval(self):
        with self.assertRaises(ValueError):
            record_decision(sample("POSSIBLE_CONFLICT"),"sense-abc","APPROVE","reviewer","reviewed")
    def test_duplicate_blocks_approval(self):
        with self.assertRaises(ValueError):
            record_decision(sample("POSSIBLE_DUPLICATE"),"sense-abc","APPROVE","reviewer","reviewed")
    def test_stale_value_not_exported(self):
        data=sample()
        reviews=record_decision(data,"sense-abc","APPROVE","reviewer","reviewed")
        data["candidates"][0]["meaning"]="changed"
        self.assertEqual(stage(data,reviews)["count"],0)
    def test_change_decision_not_silent(self):
        data=sample()
        reviews=record_decision(data,"sense-abc","REJECT","reviewer","reviewed")
        with self.assertRaises(ValueError):
            record_decision(data,"sense-abc","APPROVE","reviewer","reviewed",reviews)

if __name__=="__main__":
    unittest.main()
