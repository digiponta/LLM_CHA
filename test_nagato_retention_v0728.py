import json,tempfile,unittest
from pathlib import Path
from benchmark_nagato_retention_v0728 import cohort_metrics,evaluate

class NagatoRetentionTests(unittest.TestCase):
    def test_cohort_metrics(self):
        rows=[{"cohort":"old","exact":True},{"cohort":"old","exact":False},
              {"cohort":"new","exact":True}]
        result=cohort_metrics(rows)
        self.assertEqual(result["old"]["count"],2)
        self.assertEqual(result["new"]["exact"],1)
    def test_old_forgetting(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for name in ("old.pt","new.pt","base.pt","tokenizer.json"):
                (root/name).write_text(name)
            probes=root/"probes.json"
            probes.write_text(json.dumps([
                {"knowledge_id":"old","split":"train","cohort":"old","question":"旧知識","reference":"旧回答"},
                {"knowledge_id":"new","split":"train","cohort":"new","question":"新知識","reference":"新回答"}],ensure_ascii=False))
            answers={"old.pt":{"旧知識":"旧回答","新知識":"未学習"},
                     "new.pt":{"旧知識":"忘却","新知識":"新回答"}}
            result=evaluate(root/"old.pt",root/"new.pt",probes,root/"base.pt",
                root/"tokenizer.json",root/"report.json",
                factory=lambda p:lambda q:answers[Path(p).name][q])
            self.assertEqual(result["old_initial_correct"],1)
            self.assertEqual(result["old_lost"],1)
            self.assertEqual(result["old_forgetting_rate"],1.0)
            self.assertTrue(result["protected_unchanged"])
    def test_invalid_cohort(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for name in ("old.pt","new.pt","base.pt","tokenizer.json"):
                (root/name).write_text(name)
            probes=root/"probes.json"
            probes.write_text(json.dumps([{"knowledge_id":"x","split":"train",
                "cohort":"bad","question":"Q","reference":"A"}]))
            with self.assertRaises(ValueError):
                evaluate(root/"old.pt",root/"new.pt",probes,root/"base.pt",
                    root/"tokenizer.json",root/"out.json",
                    factory=lambda p:lambda q:"A")
if __name__=="__main__":unittest.main()
