import tempfile,json,unittest
from pathlib import Path
from analyze_replay25_sweep_v0135859 import summarize
class Tests(unittest.TestCase):
 def test_summary_and_review(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);runs=[]
   for budget,updates in ((24000,60),(32000,80),(40000,100)):
    p=root/str(budget);p.mkdir()
    (p/"report.json").write_text(json.dumps({"train_token_budget":budget,"updates":updates,"replay_ratio":0.25,"train_count":56}),encoding="utf-8")
    entries=[{"updates":0,"train_token_exposures":0,"replay_token_exposures":0,"validation_nll":8.7,"fit":{"token_exact":0},"holdout":{"token_exact":0},"protected_changed_ids":[],"elapsed_seconds":0,"holdout_generations":[]},
             {"updates":updates,"train_token_exposures":budget,"replay_token_exposures":budget//3,"validation_nll":3.1,"fit":{"token_exact":56},"holdout":{"token_exact":0},"protected_changed_ids":[],"elapsed_seconds":1,"holdout_generations":[{"id":"h","expected_text":"正解","generated":"回答","token_exact_body":False,"nfkc_equal":False}]}]
    (p/"metrics.jsonl").write_text("\n".join(json.dumps(x) for x in entries),encoding="utf-8")
    runs.append((budget,updates,p))
   result=summarize(runs,root/"out")
   self.assertEqual(len(result),3)
   self.assertEqual(result[0]["first_fully_safe_step"],60)
   self.assertTrue((root/"out"/"review.csv").exists())
 def test_bad_ratio_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"run";p.mkdir()
   (p/"report.json").write_text(json.dumps({"train_token_budget":24000,"updates":60,"replay_ratio":0.5,"train_count":56}),encoding="utf-8")
   with self.assertRaises(ValueError):summarize([(24000,60,p)],Path(d)/"out")
if __name__=="__main__":unittest.main()
