import json
import tempfile
import unittest
from pathlib import Path
from extract_web_candidates_v0972 import sentence_candidates, process

def record(text):
    return {"schema":"web_pending_v097","state":"PENDING_REVIEW",
            "url":"https://example.org/test","title":"Test","excerpt":text,
            "retrieved_at":"2026-10-25T00:00:00+00:00",
            "train_ready":False,"auto_promote":False}

class WebCandidateTests(unittest.TestCase):
    def test_extract_original_sentence_and_provenance(self):
        sentence="量子力学の入門資料では観測と確率に関する記述が紹介されている。"
        items=sentence_candidates(record(sentence))
        self.assertEqual(items[0]["text"],sentence)
        self.assertEqual(items[0]["source_url"],"https://example.org/test")
    def test_always_pending(self):
        item=sentence_candidates(record("これは事実を検証する前の出典に由来する長めのテキストである。"))[0]
        self.assertEqual(item["state"],"PENDING_REVIEW")
        self.assertFalse(item["train_ready"])
        self.assertFalse(item["auto_promote"])
        self.assertFalse(item["semantic_memory_approved"])
        self.assertEqual(item["rights_state"],"UNKNOWN")
    def test_duplicate_extraction_is_deduplicated(self):
        text="十分な長さを持つ検証前の文章として扱う必要がある。"
        self.assertEqual(len(sentence_candidates(record(text+" "+text))),1)
    def test_short_fragment_rejected(self):
        self.assertEqual(sentence_candidates(record("Hello.")),[])
    def test_invalid_state_rejected(self):
        r=record("十分な長さを持つ検証前の文章として扱う必要がある。")
        r["train_ready"]=True
        with self.assertRaises(ValueError):
            sentence_candidates(r)
    def test_jsonl_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"input.jsonl"
            o=Path(tmp)/"output.jsonl"
            r=record("量子力学の入門資料では観測と確率に関する記述が紹介されている。")
            p.write_text(json.dumps(r,ensure_ascii=False)+"\n",encoding="utf-8")
            result=process(p,o)
            self.assertEqual(result["candidate_count"],1)
            self.assertEqual(json.loads(o.read_text(encoding="utf-8"))["schema"],
                             "web_semantic_candidate_v0972")
    def test_reject_same_input_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"same.jsonl"
            p.write_text("",encoding="utf8")
            with self.assertRaises(ValueError):
                process(p,p)

if __name__=="__main__":unittest.main()
