import json,tempfile,hashlib,unittest
from pathlib import Path
from preflight_real_persona_training_v013588295 import preflight
class TrainingPreflightTests(unittest.TestCase):
 def test_blocks_without_review(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);base=d/"base.pt";base.write_bytes(b"base")
   data=d/"pilot.jsonl";data.write_text(json.dumps({"user":"おはよう","assistant":"こんにちは","source":"chat-manual"},ensure_ascii=False)+"\n",encoding="utf-8")
   hold=d/"holdout.json";hold.write_text(json.dumps({"cases":[]}))
   result=preflight(data,d/"missing.json",hold,base,d/"new.pt",d/"state.json")
   self.assertEqual(result["status"],"BLOCKED")
   self.assertIn("REVIEW_FILE_MISSING",result["errors"])
 def test_explicit_reviews_and_hash(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);base=d/"base.pt";base.write_bytes(b"base")
   data=d/"pilot.jsonl";data.write_text(json.dumps({"user":"おはよう","assistant":"こんにちは","source":"chat-manual"},ensure_ascii=False)+"\n",encoding="utf-8")
   hold=d/"holdout.json";hold.write_text(json.dumps({"cases":[]}))
   reviews={x:True for x in ("license_checked","privacy_sample_reviewed","persona_separation_approved","quality_sample_approved")}
   reviews["dataset_sha256"]=hashlib.sha256(data.read_bytes()).hexdigest()
   review=d/"review.json";review.write_text(json.dumps(reviews))
   result=preflight(data,review,hold,base,d/"candidate.pt",d/"state.json")
   self.assertEqual(result["status"],"READY")
   (d/"candidate.pt").write_bytes(b"existing")
   result=preflight(data,review,hold,base,d/"candidate.pt",d/"state.json")
   self.assertEqual(result["status"],"BLOCKED")
if __name__=="__main__":unittest.main()
