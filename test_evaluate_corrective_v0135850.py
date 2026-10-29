import hashlib,json,tempfile,unittest
from pathlib import Path
from evaluate_corrective_v0135850 import inspect,prepare

def write_jsonl(path,rows):
    path.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
class Tests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory()
    root=Path(self.tmp.name)
    self.source=root/"source.jsonl";self.correction=root/"correction.jsonl"
    self.report=root/"report.json";self.output=root/"out"
    rows=[
      {"id":"t","split":"train","user":"こんにちは","assistant":"やあ。"},
      {"id":"trained-repair","split":"train","user":"疲れたよ","assistant":"休めそう？"},
      {"id":"h","split":"holdout","user":"最近どう？","assistant":"元気だよ。"},
      {"id":"p","split":"protected","user":"あなたは誰","assistant":"長門有希。"}]
    write_jsonl(self.source,rows)
    write_jsonl(self.correction,[{"id":"r","source_id":"old-h","user":"疲れたよ","assistant":"休めそう？"}])
    r={"source_sha256":hashlib.sha256(self.source.read_bytes()).hexdigest(),
      "candidate_sha256":"unused","holdout_before":[{"id":"h","generated":"ああ"}],
      "holdout_after":[{"id":"h","generated":"変な答え"}],"protected_changed_ids":[]}
    self.report.write_text(json.dumps(r),encoding="utf-8")
 def tearDown(self):self.tmp.cleanup()
 def test_create_review_queue(self):
    result=prepare(self.report,self.source,self.correction,self.output)
    self.assertEqual(result["candidate_count"],1)
    proposals=(self.output/"review_candidates.jsonl").read_text(encoding="utf-8")
    self.assertIn('"approved_for_training": false',proposals)
    self.assertEqual(result["retired_holdout_retention"],[])
 def test_report_mismatch(self):
    r=json.loads(self.report.read_text())
    r["source_sha256"]="wrong"
    self.report.write_text(json.dumps(r))
    with self.assertRaises(ValueError):inspect(self.report,self.source,self.correction)
 def test_corrective_retention_source_required(self):
    write_jsonl(self.correction,[{"id":"r","source_id":"old-h","user":"missing","assistant":"wrong"}])
    with self.assertRaises(ValueError):inspect(self.report,self.source,self.correction)
 def test_no_overwrite(self):
    self.output.mkdir()
    with self.assertRaises(FileExistsError):prepare(self.report,self.source,self.correction,self.output)
if __name__=="__main__":unittest.main()
