import json
import tempfile
import unittest
from pathlib import Path
from build_replay_dataset_v013582 import candidates, audit_review

class DatasetTests(unittest.TestCase):
    def sources(self, d):
        sources={}
        for domain in ("conversation","persona","knowledge"):
            p=d/(domain+".jsonl")
            row={"user":domain+" の質問","assistant":domain+" の回答"}
            p.write_text(json.dumps(row,ensure_ascii=False)+"\n",encoding="utf-8")
            sources[domain]=p
        val=d/"val.jsonl"
        val.write_text(json.dumps({"user":"別の質問","assistant":"別の回答"},ensure_ascii=False)+"\n",encoding="utf-8")
        return sources,val
    def test_three_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            sources,val=self.sources(Path(d))
            rows,stats=candidates(sources,[val])
            self.assertEqual(len(rows),3)
            self.assertEqual(sum(x["candidate_count"] for x in stats.values()),3)
    def test_holdout_question_block(self):
        with tempfile.TemporaryDirectory() as d:
            sources,val=self.sources(Path(d))
            val.write_text(json.dumps({"user":"persona の質問","assistant":"異なる回答"},ensure_ascii=False)+"\n",encoding="utf-8")
            rows,stats=candidates(sources,[val])
            self.assertEqual(len(rows),2)
            self.assertEqual(stats["persona"]["blocked_by_reserved"],1)
    def test_pending_review_fails(self):
        with tempfile.TemporaryDirectory() as d:
            sources,val=self.sources(Path(d))
            rows,_=candidates(sources,[val])
            with self.assertRaises(ValueError):audit_review(rows,rows,[val])
    def test_reviewed_persona_approval(self):
        with tempfile.TemporaryDirectory() as d:
            sources,val=self.sources(Path(d))
            rows,_=candidates(sources,[val])
            for row in rows:
                row["approved"]=True
                if row["domain"]=="persona":row["persona_reviewed"]=True
            out,stats=audit_review(rows,rows,[val])
            self.assertEqual(stats["approved"],3)
            self.assertEqual(len(out["persona"]),1)
    def test_persona_requires_review(self):
        with tempfile.TemporaryDirectory() as d:
            sources,val=self.sources(Path(d))
            rows,_=candidates(sources,[val])
            for row in rows:
                row["approved"]=True
            with self.assertRaises(ValueError):audit_review(rows,rows,[val])

if __name__=="__main__":
    unittest.main()
