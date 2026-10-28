import json,tempfile,unittest
from pathlib import Path
from text_integrity_gate_v0135837 import defects,validate_training_records,audit

class Tests(unittest.TestCase):
 def test_replacement_character_rejected(self):
  self.assertEqual(defects("�責が好き。"),["REPLACEMENT_CHARACTER_U_FFFD"])
  self.assertEqual(defects("夏目漱石。"),[])
 def test_training_record_exclusion(self):
  rows=[{"id":"ok","user":"作者は？","assistant":"夏目漱石。"},
        {"id":"bad","user":"作者は？","assistant":"�責が好き。"}]
  good,bad=validate_training_records(rows)
  self.assertEqual([r["id"] for r in good],["ok"])
  self.assertEqual(bad[0]["id"],"bad")
 def test_control_character(self):
  self.assertIn("ILLEGAL_CONTROL_CHARACTER",defects("A\x00B"))
 def test_report_quarantine_without_deletion(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   source=root/"input.jsonl";source.write_text(json.dumps({"id":"ok","user":"作者","assistant":"漱石"},ensure_ascii=False)+"\n",encoding="utf-8")
   generated=root/"raw.json";generated.write_text(json.dumps({"events":[{"id":"lit-theme","round":2,"answer":"�責が好き。"}]},ensure_ascii=False),encoding="utf-8")
   before=generated.read_bytes()
   report=audit(source,root/"audit.json",generated)
   self.assertEqual(report["safe_records"],1)
   self.assertEqual(len(report["generation_quarantine"]),1)
   self.assertEqual(generated.read_bytes(),before)
 def test_invalid_utf8_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/"bad.jsonl";source.write_bytes(b"\xff")
   with self.assertRaises(UnicodeDecodeError):audit(source,root/"audit.json")
if __name__=="__main__":unittest.main()
