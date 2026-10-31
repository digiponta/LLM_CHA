import json,tempfile,unittest
from pathlib import Path
from inspect_real_persona_v013588290 import inspect
class AuditTests(unittest.TestCase):
    def test_missing_directory(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(inspect(Path(d)/"absent")["status"],"MISSING_LOCAL_DIRECTORY")
    def test_jsonl_keys_without_content(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"dialogs.jsonl"
            p.write_text(json.dumps({"user":"secret message","assistant":"private answer"},ensure_ascii=False)+"\n",encoding="utf-8")
            report=inspect(d)
            self.assertEqual(report["recognized_files"][0]["first_record_keys"],["user","assistant"])
            self.assertNotIn("secret message",json.dumps(report))
            self.assertFalse(report["training_started"])
if __name__=="__main__":unittest.main()
