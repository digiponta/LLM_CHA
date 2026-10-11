import tempfile,unittest
from pathlib import Path
from corpus_context_classification_v023367 import mentions,MentionStore,classify

class ContextMentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/"sample.txt"
        self.p.write_text("量子力学で考えると、そうかもしれない。\n量子力学的な見方は、映像のようなもの。\n量子力学は物理学の分野である。\n",encoding="utf8")
    def test_all_appearances(self):
        self.assertEqual(len(mentions(self.p,"量子力学")),3)
    def test_bytes(self):
        raw=self.p.read_bytes()
        for row in mentions(self.p,"量子力学"):
            self.assertEqual(raw[row["mention_start"]:row["mention_end"]].decode("utf8"),"量子力学")
    def test_labels(self):
        rows=mentions(self.p,"量子力学")
        self.assertIn("HYPOTHESIS",rows[0]["labels"])
        self.assertIn("ANALOGY",rows[1]["labels"])
        self.assertIn("STRUCTURAL_CANDIDATE",rows[2]["labels"])
    def test_repeat_mentions_one_sentence(self):
        self.p.write_text("量子力学と量子力学を比較する。",encoding="utf8")
        self.assertEqual(len(mentions(self.p,"量子力学")),2)
    def test_store_and_dedup(self):
        s=MentionStore(Path(self.tmp.name)/"mentions.sqlite3")
        self.assertEqual(len(s.scan("ctx","量子力学",self.p)),3)
        self.assertEqual(len(s.scan("ctx","量子力学",self.p)),3)
        self.assertEqual(len(s.list("ctx","量子力学")),3)
    def test_context_isolation(self):
        s=MentionStore(Path(self.tmp.name)/"mentions.sqlite3")
        s.scan("ctx","量子力学",self.p)
        self.assertEqual(s.list("other","量子力学"),[])
    def test_no_promotions(self):
        s=MentionStore(Path(self.tmp.name)/"mentions.sqlite3")
        s.scan("ctx","量子力学",self.p)
        self.assertEqual({r["status"] for r in s.list("ctx","量子力学")},{"PENDING"})
    def test_invalid_utf8(self):
        self.p.write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError):mentions(self.p,"量子力学")
    def test_source_unmodified(self):
        before=self.p.read_bytes()
        MentionStore(Path(self.tmp.name)/"mentions.sqlite3").scan("ctx","量子力学",self.p)
        self.assertEqual(before,self.p.read_bytes())
    def test_limit(self):
        self.assertEqual(len(mentions(self.p,"量子力学",limit=2)),2)

if __name__=="__main__":unittest.main()
