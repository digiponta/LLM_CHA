import tempfile,unittest,json
from pathlib import Path
from curate_inline_ruby_v01349 import validate_rules,apply,curate
class CurateTests(unittest.TestCase):
    def test_review_required(self):
        with self.assertRaises(ValueError):validate_rules({"rules":[{"surface":"見て","replacement":"見","reason":"guess"}]})
    def test_exact_only(self):
        rows,changes=apply(["吾輩わがはいは猫である。","見ると云って帰った。"],
          [("吾輩わがはい","吾輩","manual confirmation")])
        self.assertEqual(rows[0],"吾輩は猫である。")
        self.assertEqual(rows[1],"見ると云って帰った。")
        self.assertEqual(len(changes),1)
    def test_duplicate_rejected(self):
        rule={"surface":"吾輩わがはい","replacement":"吾輩","reason":"verified","reviewed":True}
        with self.assertRaises(ValueError):validate_rules({"rules":[rule,rule]})
    def test_report_and_immutable_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);source=p/"source.txt";rules=p/"rules.json"
            original="吾輩わがはいは猫である。\n見ると云って帰った。\n"
            source.write_text(original,encoding="utf8")
            rules.write_text(json.dumps({"rules":[{"surface":"吾輩わがはい",
                "replacement":"吾輩","reviewed":True,"reason":"manually confirmed"}]}),encoding="utf8")
            meta=curate(source,rules,p/"out.txt",p/"audit.json")
            self.assertFalse(meta["training_approved"])
            self.assertEqual(meta["replacements"],1)
            self.assertEqual(source.read_text(encoding="utf8"),original)
    def test_prevent_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);source=p/"source.txt";rules=p/"rules.json"
            source.write_text("abc",encoding="utf8")
            rules.write_text('{"rules":[]}',encoding="utf8")
            (p/"out.txt").write_text("already")
            with self.assertRaises(FileExistsError):curate(source,rules,p/"out.txt",p/"audit.json")
if __name__=="__main__":unittest.main()
