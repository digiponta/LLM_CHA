import tempfile,unittest
from pathlib import Path
from daily_conversation_foundation_v09728 import dataset,audit
from prepare_daily_conversation_v09728 import export

class DailyConversationTests(unittest.TestCase):
    def test_train_holdout_disjoint(self):
        d=dataset();a=audit(d)
        self.assertTrue(a["ready_for_controlled_training"])
        self.assertEqual(a["train_count"],30)
        self.assertEqual(a["holdout_count"],12)
        self.assertEqual(a["train_holdout_overlap"],[])
    def test_labels_and_provenance(self):
        rows=dataset()["train"]
        self.assertTrue(all(r["target"] and r["input"] for r in rows))
        self.assertTrue(all(r["provenance"]=="CURATED_SYNTHETIC" for r in rows))
        self.assertEqual(len({r["semantic"]["emotion"] for r in rows}),6)
    def test_export_split_files(self):
        with tempfile.TemporaryDirectory() as folder:
            stats=export(folder)
            self.assertTrue((Path(folder)/"daily_conversation_train_v09728.jsonl").exists())
            self.assertEqual(stats["holdout_count"],12)
            self.assertEqual(len((Path(folder)/"daily_conversation_holdout_v09728.jsonl").read_text(encoding="utf-8").splitlines()),12)
    def test_no_training_automatic(self):
        self.assertFalse(dataset()["train_ready"])
        self.assertFalse(dataset()["auto_promote"])
if __name__=="__main__":unittest.main()
