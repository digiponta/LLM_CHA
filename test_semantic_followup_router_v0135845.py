import json,tempfile,unittest
from pathlib import Path
from semantic_followup_router_v0135845 import followup,route,explicit_subject,audit
def create(root):
 p=root/"p.jsonl";t=root/"t.jsonl";m=root/"m.json"
 p.write_text('{"subject":"吾輩は猫である","value":"夏目漱石"}\n',encoding="utf-8")
 t.write_text('{"concept":"吾輩は猫である","state":"TRUE"}\n',encoding="utf-8")
 m.write_text(json.dumps({"format":"cha-runtime-adapter-manifest-v0.13.58.42","records":[
 {"record_id":"a","subject":"吾輩は猫である","relation":"author","value":"夏目漱石","source_id":"lit-author",
 "approval_state":"ASSISTANT_REVIEWED_EXPERIMENTAL","active":True,"production_approved":False}]},ensure_ascii=False),encoding="utf-8")
 return {"LLM_CHA_SEMANTIC_RUNTIME":"1","LLM_CHA_SEMANTIC_PROPOSITIONS":str(p),
 "LLM_CHA_SEMANTIC_TRUTH":str(t),"LLM_CHA_SEMANTIC_MANIFEST":str(m)}
class Tests(unittest.TestCase):
 def test_followup(self):
  self.assertIn("作者",followup("その作者は？","吾輩は猫である"))
  self.assertIsNone(followup("その作者は？",None))
 def test_session_and_reload(self):
  with tempfile.TemporaryDirectory() as d:
   env=create(Path(d))
   first=route("『吾輩は猫である』の作者は？",None,env)
   self.assertIsNotNone(first)
   second=route("その作者は？",first["subject"],env)
   self.assertIn("夏目漱石",second["result"]["answer"])
   Path(env["LLM_CHA_SEMANTIC_PROPOSITIONS"]).write_text("",encoding="utf-8")
   self.assertIsNone(route("その作者は？",first["subject"],env))
 def test_default_off(self):
  self.assertIsNone(route("その作者は？","吾輩は猫である",{}))
 def test_audit_metadata(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/"audit.jsonl"
   audit({"route":"EXPERIMENTAL_SEMANTIC","source_ids":["a"]},{"LLM_CHA_SEMANTIC_AUDIT":str(f)})
   self.assertEqual(json.loads(f.read_text(encoding="utf-8"))["source_ids"],["a"])
if __name__=="__main__":unittest.main()
