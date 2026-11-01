import tempfile,unittest
from pathlib import Path
from rse_candidate_lifecycle_v013588322 import register,review
from rse_live_route_v013588323 import decide_live_route

Q="少しお話ししませんか？"
A="もちろん。何について話しましょう？"

class LiveRouteTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.store=Path(self.tmp.name)/"rse.json"
 def test_unapproved_fail_closed(self):
  register(self.store,"invite",Q,A,"curated")
  x=decide_live_route(Q,self.store)
  self.assertEqual((x["route"],x["answer"]),("RSE_UNLEARNED_EXPERIMENTAL","未学習です"))
 def test_approved_candidate(self):
  register(self.store,"invite",Q,A,"curated")
  review(self.store,"invite","APPROVED","reviewer")
  x=decide_live_route(Q,self.store)
  self.assertEqual((x["answer"],x["route"]),(A,"RSE_APPROVED_EXPERIMENTAL"))
 def test_revoke(self):
  register(self.store,"invite",Q,A,"curated")
  review(self.store,"invite","APPROVED","reviewer")
  review(self.store,"invite","REVOKED","reviewer")
  self.assertEqual(decide_live_route(Q,self.store)["answer"],"未学習です")
 def test_current_activity_abstain(self):
  self.assertEqual(decide_live_route("今何してる？",self.store)["answer"],"未学習です")
 def test_factual_not_intercepted(self):
  self.assertIsNone(decide_live_route("閃亜鉛鉱とは",self.store))
 def test_other_smalltalk_not_intercepted(self):
  self.assertIsNone(decide_live_route("今日はいい天気です",self.store))
 def test_corrupt_store_fails_closed(self):
  self.store.write_text("{broken",encoding="utf-8")
  self.assertEqual(decide_live_route(Q,self.store)["route"],"RSE_STORE_ERROR_EXPERIMENTAL")
if __name__=="__main__":unittest.main()
