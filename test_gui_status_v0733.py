import unittest
from gui_status_v0732 import parse_status,StatusParser

class GUIStatusV0733Tests(unittest.TestCase):
    def test_restore_count(self):
        r=parse_status("[experimental startup restore: status=RESTORED, checked=1, candidate_count=11, checkpoint=x]")
        self.assertEqual(r["candidate"],"Candidates: 11 PENDING")
        self.assertEqual(r["experimental"],"Experimental: RESTORED")
    def test_route_wikipedia(self):
        r=parse_status("[route=UNKNOWN_WIKIPEDIA_FALLBACK, term=ネコ, truth_state=EXTERNAL_UNVERIFIED]")
        self.assertIn("UNKNOWN_WIKIPEDIA_FALLBACK",r["route"])
        self.assertIn("unverified",r["route"])
    def test_route_raw(self):
        r=parse_status("[route=RAW_CONCEPT_EVIDENCE, concept=時間, truth_state=UNVERIFIED]")
        self.assertIn("unverified",r["route"])
    def test_persona_no_status(self):
        self.assertEqual(parse_status("[persona_audit={}]"),{})
    def test_split_stream(self):
        events=[]
        parser=StatusParser(events.append)
        parser.feed("[experimental startup restore: status=RESTORED, ")
        parser.feed("candidate_count=11]\n")
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["candidate"],"Candidates: 11 PENDING")
if __name__=="__main__":unittest.main()
