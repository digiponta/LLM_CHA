import unittest
from candidate_response_validation_v0713 import validate_candidate_response,candidate_answer_fallback

RECORD={"id":"candidate:1","question":"v072実験の合言葉は何ですか",
        "answer":"候補の実験回答です。","source_id":"sandbox:v072","status":"PENDING"}

class CandidateResponseValidationTests(unittest.TestCase):
    def test_exact_registered_answer_accepted_as_unverified(self):
        result=candidate_answer_fallback(RECORD["question"],lambda q:RECORD["answer"],RECORD)
        self.assertEqual(result["route"],"EXPERIMENTAL_FALLBACK")
        self.assertEqual(result["truth_state"],"EXPERIMENTAL_UNVERIFIED")
        self.assertEqual(result["reason"],"candidate_exact_consistency")
        self.assertFalse(result["auto_promote"])
    def test_mutated_answer_rejected(self):
        result=candidate_answer_fallback(RECORD["question"],lambda q:"候補の実験回答回答回答です。",RECORD)
        self.assertEqual(result["route"],"EXPERIMENTAL_REJECTED")
    def test_fluent_but_unregistered_answer_rejected(self):
        result=candidate_answer_fallback(RECORD["question"],lambda q:"v072実験の答えは別の回答です。",RECORD)
        self.assertEqual(result["reason"],"candidate_answer_mismatch")
    def test_wrong_question_rejected(self):
        result=validate_candidate_response("別の質問",RECORD["answer"],RECORD)
        self.assertFalse(result["accepted"])
    def test_approved_record_not_eligible(self):
        result=validate_candidate_response(RECORD["question"],RECORD["answer"],dict(RECORD,status="APPROVED"))
        self.assertFalse(result["accepted"])
    def test_empty_rejected(self):
        self.assertFalse(validate_candidate_response(RECORD["question"],"",RECORD)["accepted"])
if __name__=="__main__":unittest.main()
