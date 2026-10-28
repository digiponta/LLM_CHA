import json,tempfile,unittest
from pathlib import Path
from semantic_chat_optin_v0135843 import load_sources,respond
def write(path,rows,bom=False):
 path.write_bytes(("\ufeff" if bom else "").encode("utf-8")+("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n").encode("utf-8"))
class Tests(unittest.TestCase):
 def test_absent(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);s=load_sources(root/"p",root/"t",root/"m")
   self.assertEqual(s["status"],"NOT_INITIALIZED")
   self.assertEqual(respond("作者は誰？",s)["status"],"ABSTAIN")
 def test_bom_and_plain(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/"p";t=root/"t";m=root/"m"
   write(p,[{"subject":"吾輩は猫である","value":"夏目漱石"}],bom=True)
   write(t,[{"concept":"吾輩は猫である","state":"TRUE"}],bom=True)
   m.write_text(json.dumps({"format":"cha-runtime-adapter-manifest-v0.13.58.42","records":[
    {"record_id":"a","subject":"吾輩は猫である","relation":"author","value":"夏目漱石",
     "source_id":"lit-author","approval_state":"ASSISTANT_REVIEWED_EXPERIMENTAL","active":True,"production_approved":False}
    ]},ensure_ascii=False),encoding="utf-8")
   s=load_sources(p,t,m)
   self.assertEqual(s["status"],"READY")
   self.assertIn("夏目漱石",respond("『吾輩は猫である』の著者は？",s)["answer"])
 def test_missing_approval(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/"p";t=root/"t"
   write(p,[]);write(t,[])
   self.assertEqual(load_sources(p,t,root/"missing")["status"],"NO_EXPLICIT_APPROVAL_MANIFEST")
 def test_invalid_utf8(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/"p";t=root/"t";m=root/"m"
   p.write_bytes(b"\xff");write(t,[]);m.write_text("{}")
   with self.assertRaises(UnicodeDecodeError):load_sources(p,t,m)
if __name__=="__main__":unittest.main()
