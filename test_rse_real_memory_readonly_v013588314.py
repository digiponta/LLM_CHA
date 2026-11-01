import json,tempfile,unittest
from pathlib import Path
from rse_real_memory_readonly_v013588314 import adapt,run
class BridgeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.u=Path(self.tmp.name)/"unified.jsonl"
  self.t=Path(self.tmp.name)/"truth.jsonl"
 def write(self,u,truth):
  self.u.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in u),encoding="utf-8")
  self.t.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in truth),encoding="utf-8")
 def test_true_not_approval(self):
  self.write([{"concept":"猫","assistant":"猫は哺乳類"}],[{"concept":"猫","state":"TRUE"}])
  records,stats=adapt(self.u,self.t)
  self.assertFalse(records[0]["approved"])
  self.assertEqual(stats["explicitly_approved_and_true"],0)
 def test_approved_not_truth(self):
  self.write([{"concept":"猫","assistant":"猫は哺乳類","approved":True}],[])
  x=run("猫とは",self.u,self.t,[])
  self.assertEqual(x["answer"],"未学習です")
 def test_approved_true(self):
  self.write([{"concept":"猫","assistant":"猫は哺乳類","approved":True}],[{"concept":"猫","state":"TRUE"}])
  x=run("猫とは",self.u,self.t,[])
  self.assertEqual(x["status"],"MEMORY_SELECTED")
  self.assertTrue(x["read_only"])
 def test_missing_stores(self):
  x=run("猫とは",self.u,self.t,[])
  self.assertEqual(x["status"],"UNLEARNED")
if __name__=="__main__":unittest.main()
