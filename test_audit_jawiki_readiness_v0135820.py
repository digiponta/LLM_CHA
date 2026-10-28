import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from audit_jawiki_readiness_v0135820 import evaluate

class MockTokenizer:
 def encode(self,s,add_bos=False,add_eos=False):
  return list(range(len(s)//2+1))
class MockTokenizerType:
 @staticmethod
 def load(_):return MockTokenizer()

class Tests(unittest.TestCase):
 def setup_case(self,root,text="日本語の長い文章です。"*12):
  source=root/"candidates.jsonl";quality=root/"quality.json";tokenizer=root/"tokenizer.json"
  row={"article_id":"42","title":"日本語","source_url":"https://ja.wikipedia.org/?curid=42","text":text,"approval":"PENDING_REVIEW","auto_promote":False}
  source.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf8")
  quality.write_text(json.dumps({"sha256":{"clean_candidates.jsonl":hashlib.sha256(source.read_bytes()).hexdigest()}}),encoding="utf8")
  tokenizer.write_text("{}",encoding="utf8")
  return source,quality,tokenizer
 def test_valid_but_not_training_approved(self):
  with tempfile.TemporaryDirectory() as d,patch("tokenizer_bpe.Tokenizer",MockTokenizerType):
   a,b,c=self.setup_case(Path(d));r=evaluate(a,b,c,Path(d)/"result.json")
   self.assertEqual(r["valid_records"],1)
   self.assertTrue(r["quality_check_pass"])
   self.assertEqual(r["status"],"NOT_READY")
   self.assertFalse(r["production_promotion_allowed"])
 def test_detect_markup(self):
  with tempfile.TemporaryDirectory() as d,patch("tokenizer_bpe.Tokenizer",MockTokenizerType):
   a,b,c=self.setup_case(Path(d),text="日本語の長い文章です。"*12+"]]")
   r=evaluate(a,b,c,Path(d)/"result.json")
   self.assertEqual(r["flagged_records"],1)
 def test_reject_sha_mismatch(self):
  with tempfile.TemporaryDirectory() as d:
   a,b,c=self.setup_case(Path(d));a.write_text("tampered",encoding="utf8")
   with self.assertRaises(ValueError):evaluate(a,b,c,Path(d)/"result.json")
 def test_nonoverwrite(self):
  with tempfile.TemporaryDirectory() as d,patch("tokenizer_bpe.Tokenizer",MockTokenizerType):
   a,b,c=self.setup_case(Path(d));out=Path(d)/"result.json"
   evaluate(a,b,c,out)
   with self.assertRaises(FileExistsError):evaluate(a,b,c,out)
if __name__=="__main__":unittest.main()
