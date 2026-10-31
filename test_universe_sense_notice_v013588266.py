import json
import tempfile
import unittest
from pathlib import Path
from chat_grounded_bridge_v013588264 import answer
from evidence_universe_sense_v013588266 import resolve_universe

def ev(text):
    return {"status":"EVIDENCE","topic":"宇宙","excerpt":text,
            "url":"https://ja.wikipedia.org/wiki/宇宙"}
UNIVERSE="英語 universe はラテン語 universum に由来し、すべての物と事象の総体を意味する。"
SPACE="英語 outer space は、地球の大気圏外の空間を指し、日本語では宇宙空間と呼ぶことが一般的である。"

class UniverseSenseNoticeTests(unittest.TestCase):
 def test_universe_preferred_over_space(self):
  r=resolve_universe("宇宙とは",ev(SPACE+UNIVERSE))
  self.assertEqual(r["sense"],"UNIVERSE")
  self.assertIn("語義の注意",r["answer"])
  self.assertIn("すべての物と事象",r["answer"])
 def test_outer_space_explicit(self):
  r=resolve_universe("宇宙空間とは",ev(SPACE+UNIVERSE))
  self.assertEqual(r["sense"],"OUTER_SPACE")
 def test_only_space_answers_with_caution(self):
  r=resolve_universe("宇宙とは",ev(SPACE))
  self.assertEqual(r["sense"],"OUTER_SPACE_ONLY")
  self.assertIn("定義は、この抜粋からは確認できません",r["answer"])
 def test_no_evidence_no_answer(self):
  self.assertIsNone(resolve_universe("宇宙とは",ev("宇宙についての説明はない。")))
 def test_bridge_reads_same_source_without_writes(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"evidence.json"
   p.write_text(json.dumps({"cases":[{"id":"x","question":"宇宙とは","source":{"title":"宇宙"},
      "evidence":ev(SPACE+UNIVERSE),"review":{"status":"PENDING_HUMAN_REVIEW"}}]},ensure_ascii=False),encoding="utf-8")
   before=p.read_bytes()
   r=answer("宇宙とは",p)
   self.assertEqual(r["status"],"BOUND_SENSE_NOTICE")
   self.assertIn("人手レビュー未承認",r["answer"])
   self.assertEqual(p.read_bytes(),before)
if __name__=="__main__":unittest.main()
