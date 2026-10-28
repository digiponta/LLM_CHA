import json,tempfile,unittest
from pathlib import Path
from clean_jawiki_candidates_v0135819 import clean_paragraph,assess,build

class CleanerTests(unittest.TestCase):
 def test_html_entity(self):
  self.assertEqual(clean_paragraph("A &amp; B"),"A & B")
 def test_residual_markup(self):
  self.assertIn("MARKUP",assess("見出し]] "+"普通の文章"*15,20))
 def test_broken_quote(self):
  self.assertIn("UNBALANCED_QUOTE",assess("「あいうえお"*20,20))
 def test_accepted_and_quarantined(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"source.jsonl"
   records=[{"page_id":"1","title":"項目","url":"https://ja.wikipedia.org/?curid=1",
            "text":"これは十分長い自然な文章です。"*15+"\n\n"+"broken]] text",
            "approval":"PENDING_REVIEW","auto_promote":False}]
   path.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in records),encoding="utf-8")
   out=Path(d)/"out";result=build(path,out,25)
   self.assertEqual(result["accepted"],1)
   self.assertEqual(result["quarantined"],1)
   self.assertFalse(result["training_performed"])
   self.assertFalse(result["memory_promoted"])
   with self.assertRaises(FileExistsError):build(path,out,25)
 def test_reject_unapproved_source(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"source.jsonl"
   path.write_text(json.dumps({"page_id":"1","title":"test","url":"x","text":"a",
      "approval":"APPROVED","auto_promote":True}),encoding="utf8")
   with self.assertRaises(ValueError):build(path,Path(d)/"out",1)
if __name__=="__main__":unittest.main()
