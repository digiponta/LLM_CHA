import json,tempfile,unittest
from pathlib import Path
from audit_offline_replay_v0135810 import audit,read_file
class OfflineTests(unittest.TestCase):
 def test_missing_data(self):
  with tempfile.TemporaryDirectory() as d:
   r=audit(Path(d))
   self.assertEqual(r["mode"],"OFFLINE_NO_NETWORK")
   self.assertEqual(r["dataset"]["foundation"]["status"],"MISSING")
   self.assertFalse(r["training_approved"])
 def test_approved_jsonl(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"one.jsonl"
   p.write_text(json.dumps({"approved":True,"user":"こんにちは","assistant":"こんにちは。"})+"\n",encoding="utf-8")
   self.assertEqual(len(read_file(p)),1)
 def test_reject_unapproved(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"one.jsonl"
   p.write_text(json.dumps({"approved":False,"user":"a","assistant":"b"})+"\n",encoding="utf-8")
   with self.assertRaises(ValueError):read_file(p)
 def test_cache_not_used_for_training(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"results/wikipedia_curl_cache_v013589"
   path.mkdir(parents=True)
   (path/"a.json").write_text(json.dumps({"article":{"id":12,"source":"Wikitext"}}),encoding="utf-8")
   r=audit(Path(d),include_cache=True)
   self.assertEqual(r["local_wikipedia_cache"]["valid_articles"],1)
   self.assertFalse(r["training_approved"])
 def test_detect_cross_domain_dup(self):
  with tempfile.TemporaryDirectory() as d:
   base=Path(d)/"data";base.mkdir()
   (base/"replay_conversation_train.txt").write_text("同一内容。\n",encoding="utf-8")
   (base/"replay_persona_train.txt").write_text("同一内容。\n",encoding="utf-8")
   r=audit(Path(d))
   self.assertTrue(r["overlap_warnings"])
if __name__=="__main__":unittest.main()
