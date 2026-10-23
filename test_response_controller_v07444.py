import unittest
from response_controller_v07444 import controlled_response

class ResponseControllerTests(unittest.TestCase):
    def test_good_answer(self):
        r=controlled_response(lambda n:"今日は静か。")
        self.assertEqual((r.status,r.attempts),("ACCEPT",1))
    def test_bounded_retry(self):
        r=controlled_response(lambda n:"" if n==1 else "そう。",retry_limit=1)
        self.assertEqual((r.status,r.attempts),("ACCEPT",2))
    def test_bounded_failure(self):
        r=controlled_response(lambda n:"",retry_limit=2)
        self.assertEqual((r.status,r.attempts),("FALLBACK",3))
    def test_gap_does_not_auto_accept(self):
        r=controlled_response(lambda n:"元気。",persona_gap=True)
        self.assertEqual(r.status,"REVIEW_REQUIRED")
    def test_unverified_evidence_held(self):
        r=controlled_response(lambda n:"仮説だ。",route="GENERATED_EVIDENCE",truth_state="UNVERIFIED")
        self.assertEqual(r.status,"HELD")
    def test_invalid_retry_limit(self):
        with self.assertRaises(ValueError):controlled_response(lambda n:"",retry_limit=3)
    def test_trusted_route_preserved(self):
        r=controlled_response(lambda n:"既存の証拠。",persona_gap=True,route="TRUSTED_RETRIEVAL")
        self.assertEqual(r.status,"ACCEPT")

if __name__=="__main__":
    unittest.main()
