import unittest
from gui_status_v0732 import parse_status,StatusParser

class GUIStatusTests(unittest.TestCase):
    def test_trusted(self):
        got=parse_status("[Nagato Semantic Memory: corpus_records=72, subjects=56, internalized=56, pending=0]")
        self.assertEqual(got["trusted"],"Trusted: 56 internalized")
        self.assertEqual(got["trusted_pending"],"Trusted pending: 0")
    def test_restore(self):
        self.assertEqual(parse_status("[experimental startup restore: status=RESTORED, checked=1, checkpoint=x]")["experimental"],"Experimental: RESTORED")
    def test_sleep(self):
        x=parse_status("[experimental sleep: status=TRAINED, pending=11, checkpoint=x, auto_promote=False]")
        self.assertEqual(x["candidate"],"Candidates: 11 PENDING")
    def test_reload(self):
        self.assertEqual(parse_status("[experimental adapter reload: status=LOADED, reason=-]")["experimental"],"Adapter: LOADED")
    def test_not_user_text(self):
        self.assertEqual(parse_status("AI> この知識は未検証"),{})
        self.assertEqual(parse_status("You> /sleep"),{})
    def test_stream(self):
        received=[]
        p=StatusParser(received.append)
        for ch in "[experimental startup restore: status=NO_VALID_CHECKPOINT]\n":
            p.feed(ch)
        self.assertEqual(received[0]["experimental"],"Experimental: NO_VALID_CHECKPOINT")
    def test_route(self):
        x=parse_status("[retrieval-first=HIT, concept='宇宙', route=CORPUS_MEMORY, truth_state=UNVERIFIED]")
        self.assertEqual(x["route"],"Last route: CORPUS_MEMORY")
if __name__=="__main__":unittest.main()
