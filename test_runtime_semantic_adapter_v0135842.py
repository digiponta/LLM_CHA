import tempfile,unittest
from pathlib import Path
from semantic_proposition_v1090 import Proposition
from truth_state_v10103 import TruthRecord
from runtime_semantic_adapter_v0135842 import adapter,run
from provenance_semantic_memory_v0135841 import answer
def manifest():
 return [{"record_id":"r1","subject":"吾輩は猫である","relation":"author",
 "value":"夏目漱石","source_id":"lit-author",
 "approval_state":"ASSISTANT_REVIEWED_EXPERIMENTAL","active":True,"production_approved":False}]
class Tests(unittest.TestCase):
 def test_without_true_overlay_abstains(self):
  r,b=adapter([Proposition("吾輩は猫である","夏目漱石")],[],manifest())
  self.assertEqual(len(r),0)
  self.assertEqual(answer("『吾輩は猫である』の作者は誰？",r)["status"],"ABSTAIN")
 def test_with_true_overlay_and_proposition(self):
  r,b=adapter([Proposition("吾輩は猫である","夏目漱石")],
    [TruthRecord("吾輩は猫である","TRUE")],manifest())
  self.assertEqual(len(r),1)
  self.assertEqual(answer("『吾輩は猫である』の作者は誰？",r)["status"],"ANSWERED")
 def test_missing_proposition(self):
  r,b=adapter([], [TruthRecord("吾輩は猫である","TRUE")],manifest())
  self.assertIn("PROPOSITION_NOT_FOUND",b[0]["reasons"])
 def test_pending_rejected(self):
  m=manifest();m[0]["approval_state"]="PENDING"
  r,b=adapter([Proposition("吾輩は猫である","夏目漱石")],
   [TruthRecord("吾輩は猫である","TRUE")],m)
  self.assertEqual(r,[])
 def test_source_file_required(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   with self.assertRaises(FileNotFoundError):
    run(root/"missing",root/"truth",root/"manifest",root/"output")
 def test_negation_abstains(self):
  r,_=adapter([Proposition("吾輩は猫である","夏目漱石")],
   [TruthRecord("吾輩は猫である","TRUE")],manifest())
  self.assertEqual(answer("『吾輩は猫である』の作者は夏目漱石ではない？",r)["status"],"ABSTAIN")
if __name__=="__main__":unittest.main()
