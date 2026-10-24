import json
import tempfile
import unittest
from pathlib import Path
from prepare_holdout_v08023 import prepare

class BOMInputTests(unittest.TestCase):
    def test_bom_json_can_be_read(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            src=root/"curated.json"
            store=root/"store.json"
            out=root/"out.json"
            src.write_text(json.dumps({"records":[]}),encoding="utf-8-sig")
            store.write_text(json.dumps({"candidates":[]}),encoding="utf-8")
            result=prepare(src,store,out)
            self.assertEqual(result["status"],"NOT_READY")
            self.assertFalse(result["written"])
    def test_no_file_written_on_rejected_dataset(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            src=root/"curated.json"
            store=root/"store.json"
            out=root/"out.json"
            src.write_text(json.dumps({"records":[]}),encoding="utf-8-sig")
            store.write_text(json.dumps({"candidates":[]}),encoding="utf-8")
            result=prepare(src,store,out,write=True)
            self.assertFalse(out.exists())
            self.assertFalse(result["written"])

if __name__=="__main__": unittest.main()
