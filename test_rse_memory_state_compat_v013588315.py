import json,tempfile,unittest
from pathlib import Path
from rse_memory_state_compat_v013588315 import inspect,shadow
class StateCompatibilityTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.u=Path(self.temp.name)/"u.jsonl";self.t=Path(self.temp.name)/"t.jsonl"
 def write(self,rows,truth=[]):
  self.u.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows),encoding="utf-8")
  self.t.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in truth),encoding="utf-8")
 def test_present_but_unverified_not_unlearned(self):
  self.write([{"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は亜鉛の硫化鉱物である。"}])
  x=shadow("閃亜鉛鉱とは",self.u,self.t,[])
  self.assertEqual(x["status"],"MEMORY_PRESENT_UNVERIFIED")
  self.assertIsNone(x["answer"])
  self.assertEqual(x["legacy_answer_preview"],"閃亜鉛鉱は亜鉛の硫化鉱物である。")
 def test_absence_is_unlearned(self):
  self.write([])
  x=shadow("閃亜鉛鉱とは",self.u,self.t,[])
  self.assertEqual(x["status"],"UNLEARNED")
  self.assertEqual(x["answer"],"未学習です")
 def test_explicit_true(self):
  self.write([{"concept":"閃亜鉛鉱","assistant":"硫化亜鉛"}],[{"concept":"閃亜鉛鉱","state":"TRUE"}])
  self.assertEqual(inspect("閃亜鉛鉱とは",self.u,self.t)["state"],"MEMORY_VERIFIED_BY_TRUTH")
 def test_false_is_restricted(self):
  self.write([{"concept":"閃亜鉛鉱","assistant":"誤り"}],[{"concept":"閃亜鉛鉱","state":"FALSE"}])
  self.assertEqual(shadow("閃亜鉛鉱とは",self.u,self.t,[])["status"],"MEMORY_TRUTH_RESTRICTED")
 def test_theme_path_kept(self):
  self.write([])
  x=shadow("少しお話ししませんか？",self.u,self.t,[{"question":"少しお話ししませんか？","answer":"もちろん。何について話しましょう？"}])
  self.assertEqual(x["status"],"ANSWER_SELECTED")
if __name__=="__main__":unittest.main()
