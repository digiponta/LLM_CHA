import json,tempfile,unittest
from pathlib import Path
from audit_curated_delta_v01354 import audit,digest
class DeltaAuditTests(unittest.TestCase):
    def setup_case(self,p):
        before=p/"before.txt";after=p/"after.txt";metadata=p/"audit.json"
        before.write_text("肝心かんじんの話。\n見ると分かる。\n",encoding="utf-8")
        after.write_text("肝心の話。\n見ると分かる。\n",encoding="utf-8")
        meta={"version":"v0.13.53","status":"APPLIED_REVIEWED_ONLY",
          "source_sha256":digest(before),"accepted":88,"rejected":82,"unsure":1,"applied":1,
          "edits":[{"id":"L1-C0","line":1,"start":2,"end":6,"removed":"かんじん"}]}
        metadata.write_text(json.dumps(meta),encoding="utf-8")
        return before,after,metadata
    def test_valid_diff(self):
        with tempfile.TemporaryDirectory() as d:
            result=audit(*self.setup_case(Path(d)))
            self.assertEqual(result["status"],"DIFF_VERIFIED")
            self.assertEqual(result["characters_removed"],4)
            self.assertFalse(result["training_approved"])
    def test_unreviewed_change_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=self.setup_case(Path(d))
            b.write_text("肝心の話。\n別文だ。\n",encoding="utf-8")
            with self.assertRaises(ValueError):audit(a,b,c)
    def test_modified_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=self.setup_case(Path(d))
            a.write_text("変更された内容\n",encoding="utf-8")
            with self.assertRaises(ValueError):audit(a,b,c)
    def test_bad_location_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=self.setup_case(Path(d))
            j=json.loads(c.read_text());j["edits"][0]["start"]=0
            c.write_text(json.dumps(j))
            with self.assertRaises(ValueError):audit(a,b,c)
    def test_changed_line_count_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a,b,c=self.setup_case(Path(d))
            b.write_text("肝心の話。\n",encoding="utf-8")
            with self.assertRaises(ValueError):audit(a,b,c)
if __name__=="__main__":unittest.main()
