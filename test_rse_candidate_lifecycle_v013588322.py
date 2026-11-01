import tempfile,unittest
from pathlib import Path
from rse_candidate_lifecycle_v013588322 import register,review,resolve,read
Q="少しお話ししませんか？"
A="もちろん。何について話しましょう？"
class LifecycleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.p=Path(self.tmp.name)/"candidates.json"
 def test_pending_then_approved(self):
  register(self.p,"invite",Q,A,"curated-test")
  self.assertEqual(resolve(self.p,Q)["decision"]["action"],"ABSTAIN")
  review(self.p,"invite","APPROVED","operator")
  x=resolve(self.p,Q)
  self.assertEqual((x["decision"]["action"],x["decision"]["answer"]),("SELECT_RSE",A))
 def test_revocation(self):
  register(self.p,"invite",Q,A,"curated-test")
  review(self.p,"invite","APPROVED","operator")
  review(self.p,"invite","REVOKED","operator")
  self.assertEqual(resolve(self.p,Q)["decision"]["action"],"ABSTAIN")
 def test_reject_wrong_intent(self):
  register(self.p,"invite",Q,A,"curated-test")
  review(self.p,"invite","APPROVED","operator")
  x=resolve(self.p,"今何してる？")
  self.assertEqual(x["decision"]["answer"],"未学習です")
 def test_protect_existing(self):
  register(self.p,"invite",Q,A,"curated-test")
  review(self.p,"invite","APPROVED","operator")
  x=resolve(self.p,Q,"保存済みの回答","MEMORY_ATOMIC_EXACT")
  self.assertEqual(x["decision"]["action"],"PRESERVE_EXISTING")
 def test_duplicate_id_and_reapproval_blocked(self):
  register(self.p,"invite",Q,A,"curated-test")
  with self.assertRaises(ValueError):register(self.p,"invite",Q,A,"curated-test")
  review(self.p,"invite","APPROVED","operator")
  with self.assertRaises(ValueError):review(self.p,"invite","APPROVED","operator")
 def test_mutation_fails_closed(self):
  register(self.p,"invite",Q,A,"curated-test")
  review(self.p,"invite","APPROVED","operator")
  import json
  data=read(self.p);data["records"][0]["answer"]="改ざん"
  self.p.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
  self.assertEqual(resolve(self.p,Q)["decision"]["action"],"ABSTAIN")
if __name__=="__main__":unittest.main()
