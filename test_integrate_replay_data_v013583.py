import json
import tempfile
import unittest
from pathlib import Path
from integrate_replay_data_v013583 import build

class IntegrationTests(unittest.TestCase):
    def sources(self,root,foundation_count=12):
        f=root/"foundation.txt";c=root/"conv.jsonl";p=root/"persona.jsonl";k=root/"knowledge.jsonl";v=root/"val.jsonl"
        f.write_text("\n".join(f"基礎文章{i}" for i in range(foundation_count))+"\n",encoding="utf-8")
        for path,prefix,count,persona in ((c,"会話",60,False),(p,"人格",23,True),(k,"知識",7,False)):
            path.write_text("\n".join(json.dumps({"user":f"{prefix}の質問{i}","assistant":f"{prefix}の回答{i}",
               "approved":True,**({"persona_reviewed":True} if persona else {})},ensure_ascii=False)
               for i in range(count))+"\n",encoding="utf-8")
        v.write_text(json.dumps({"user":"検証専用質問","assistant":"検証専用回答"},ensure_ascii=False)+"\n",encoding="utf-8")
        return f,c,p,k,v
    def test_repeat_cap_fail_for_small_foundation(self):
        with tempfile.TemporaryDirectory() as d:
            domain,report=build(*self.sources(Path(d)),steps=100,max_repeat=2)
            self.assertFalse(report["sampling_safe"])
            self.assertEqual(report["source_counts"]["knowledge"],7)
            self.assertEqual(len(domain["conversation"]),67)
    def test_repeat_cap_pass_with_more_foundation(self):
        with tempfile.TemporaryDirectory() as d:
            _,report=build(*self.sources(Path(d),40),steps=100,max_repeat=2)
            self.assertTrue(report["sampling_safe"])
    def test_holdout_question_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            paths=self.sources(Path(d),40)
            paths[-1].write_text(json.dumps({"user":"人格の質問0","assistant":"別の回答"},ensure_ascii=False)+"\n",encoding="utf-8")
            with self.assertRaises(ValueError):build(*paths)
    def test_unapproved_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            paths=self.sources(Path(d),40)
            p=paths[1];lines=p.read_text(encoding="utf-8").splitlines()
            first=json.loads(lines[0]);first["approved"]=False;lines[0]=json.dumps(first,ensure_ascii=False)
            p.write_text("\n".join(lines)+"\n",encoding="utf-8")
            with self.assertRaises(ValueError):build(*paths)
    def test_bad_steps(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):build(*self.sources(Path(d)),steps=101)

if __name__=="__main__":unittest.main()
