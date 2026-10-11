import tempfile,unittest
from pathlib import Path
from runtime_startup_preflight_v0233772 import preflight
from chat_runtime_benchmark_v023377 import preflight_failure,SCENARIOS

class StartupPreflightTests(unittest.TestCase):
    def test_missing_assets_reported(self):
        with tempfile.TemporaryDirectory() as d:
            report=preflight(d)
            self.assertFalse(report["ok"])
            missing={x["name"] for x in report["checks"] if not x["ok"]}
            self.assertIn("model/model-llm-try-nagato-chat-v94.pt",missing)
    def test_fixture_assets_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for rel in ("model/model-llm-try-nagato-chat-v94.pt","model/tokenizer-v0.7-bpe.json","data/data-nagato.txt"):
                path=root/rel;path.parent.mkdir(exist_ok=True);path.write_bytes(b"test")
            r=preflight(root)
            self.assertTrue(all(x["ok"] for x in r["checks"] if x["kind"]=="file"))
    def test_missing_copy_does_not_score_policy(self):
        report=preflight_failure({"ok":False,"checks":[]},"copied_assets_missing")
        self.assertEqual(report["passed"],0)
        self.assertEqual(report["total"],len(SCENARIOS))
        self.assertEqual(report["diagnostic"]["phase"],"PREFLIGHT_ERROR")
        self.assertTrue(all(x["reason"]=="not_evaluated_preflight_failure" for x in report["cases"]))
    def test_distinguish_failure_cause(self):
        r=preflight_failure({"ok":False},"required_asset_or_dependency_missing")
        self.assertEqual(r["diagnostic"]["reason"],"required_asset_or_dependency_missing")
if __name__=="__main__":unittest.main()
