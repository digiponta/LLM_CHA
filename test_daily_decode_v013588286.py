import unittest
from diagnose_daily_decode_v013588286 import PROBES

class DecodeDiagnosisTests(unittest.TestCase):
    def test_probe_set_is_seen_training_only(self):
        self.assertEqual(PROBES,("おはよう","雑談しよう","相談がある"))
    def test_probes_do_not_include_holdout_questions(self):
        from pathlib import Path
        import json
        file=Path("data/daily_conversation_eval_v013588283.json")
        if not file.exists():self.skipTest("dataset not present")
        held={x["question"] for x in json.loads(file.read_text(encoding="utf-8"))["cases"]}
        self.assertFalse(held.intersection(PROBES))
if __name__=="__main__":unittest.main()
