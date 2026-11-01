import json,tempfile,unittest
from pathlib import Path
from compare_rse_runtime_theme_v013588319 import compare
class CompareTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.u=Path(self.tmp.name)/"unified.jsonl";self.truth=Path(self.tmp.name)/"truth.jsonl"
  self.u.write_text(json.dumps({"concept":"閃亜鉛鉱","assistant":"閃亜鉛鉱は、亜鉛の硫化鉱物である。","source":"atomic-proposition"},ensure_ascii=False)+"\n",encoding="utf-8")
  self.truth.write_text("",encoding="utf-8")
 def test_existing_memory_preserved(self):
  x=compare("閃亜鉛鉱とは",self.u,self.truth,[])
  self.assertEqual(x["legacy_answer_preservation"],"PRESERVED_IN_SHADOW_PREVIEW")
  self.assertEqual(x["rse_shadow"]["status"],"MEMORY_PRESENT_UNVERIFIED")
  self.assertFalse(x["chat_py_executed"])
 def test_conversation_selected(self):
  x=compare("少しお話ししませんか？",self.u,self.truth,[{"question":"少しお話ししませんか？","answer":"もちろん。何について話しましょう？"}])
  self.assertEqual(x["rse_shadow"]["status"],"ANSWER_SELECTED")
 def test_no_match_unlearned(self):
  x=compare("今何してる？",self.u,self.truth,[])
  self.assertEqual(x["rse_shadow"]["status"],"UNLEARNED")
if __name__=="__main__":unittest.main()
