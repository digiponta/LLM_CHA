import tempfile,unittest
from pathlib import Path
from compare_daily_sft_epochs_v013588288 import validate_paths,compare

def report(nll,answer):
    return {"status":"TEACHER_FORCED_TOKEN_ANALYSIS",
            "base":[{"question":"おはよう","teacher_forced_mean_nll":8.2,"teacher_forced_top1_count":4,"target_token_count":12,"greedy_first_divergence_position":4,"greedy_text":"おはよう。"}],
            "candidate":[{"question":"おはよう","teacher_forced_mean_nll":nll,"teacher_forced_top1_count":5,"target_token_count":12,"greedy_first_divergence_position":4,"greedy_text":answer}]}
class EpochExperimentTests(unittest.TestCase):
    def test_path_collision(self):
        with self.assertRaises(ValueError):
            validate_paths("base.pt","candidate.pt","candidate.pt","a.json","b.json")
    def test_base_required(self):
        with self.assertRaises(FileNotFoundError):
            validate_paths("missing.pt","two.pt","four.pt","a.json","b.json")
    def test_distinct_paths(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/"base.pt";base.write_bytes(b"not-real-model")
            x=validate_paths(base,Path(d)/"two.pt",Path(d)/"four.pt",Path(d)/"s2.json",Path(d)/"s4.json")
            self.assertEqual(x["status"],"PATHS_ISOLATED")
    def test_compare(self):
        x=compare(report(3.0,"A"),report(2.5,"B"))
        self.assertAlmostEqual(x["rows"][0]["nll_delta_4_minus_2"],-0.5)
        self.assertFalse(x["holdout_naturalness_evaluated"])
    def test_invalid_status(self):
        with self.assertRaises(ValueError):compare({"status":"OTHER"},{})
if __name__=="__main__":unittest.main()
