import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from grounded_generation_diagnostics_v01322 import make_record, append_record

class GroundedDiagnosticTests(unittest.TestCase):
    def test_fallback_record(self):
        evidence={"knowledge_id":"raw-1","subject":"時間","source_text":"時間についての原文。"}
        generated=SimpleNamespace(text="根拠なし",token_count=9,mean_confidence=.2,
                                  min_confidence=.1,mean_top2_margin=.03)
        decision={"route":"SOURCE_QUOTATION_FALLBACK","validation":"NOT_VERBATIM_SOURCE_EXCERPT",
                  "answer":"【未承認】時間についての原文。"}
        record=make_record("時間とは",evidence,generated,decision,"candidate.pt")
        self.assertFalse(record["accepted"])
        self.assertEqual(record["generated_tokens"],9)
        self.assertEqual(record["raw_generation"],"根拠なし")
        self.assertEqual(record["truth_state"],"UNVERIFIED")
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"results"/"diagnostics.jsonl"
            append_record(path,record)
            append_record(path,record)
            rows=[json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0]["knowledge_id"],"raw-1")
if __name__=="__main__":unittest.main()
