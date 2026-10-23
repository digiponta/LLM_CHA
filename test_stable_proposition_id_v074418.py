import json
import tempfile
import unittest
from pathlib import Path
from subject_keyed_corpus_memory_v101216 import (
    CorpusMemoryRecord, normalize_record, stable_proposition_id,
    save_memory, load_memory, lookup_subject,
)
from corpus_cursor_bridge_v074417 import bridge_records

class StablePropositionIdTests(unittest.TestCase):
    def row(self, statement="宇宙は膨張する。"):
        return {"subject":"宇宙","statement":statement,"relation":"is",
                "object_description":"","source_text":statement,"source":"data-nagato.txt"}
    def test_same_content_same_id(self):
        a=normalize_record(self.row())
        b=normalize_record(self.row())
        self.assertEqual(a.proposition_id,b.proposition_id)
        self.assertTrue(a.proposition_id.startswith("cp-"))
    def test_different_content_distinct_id(self):
        self.assertNotEqual(normalize_record(self.row()).proposition_id,
                            normalize_record(self.row("宇宙には銀河がある。")).proposition_id)
    def test_legacy_jsonl_load_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"memory.jsonl"
            path.write_text(json.dumps(self.row(),ensure_ascii=False)+"\n",encoding="utf-8")
            first=load_memory(path)
            self.assertTrue(first[0].proposition_id)
            save_memory(path,first)
            second=load_memory(path)
            self.assertEqual(first[0].proposition_id,second[0].proposition_id)
            self.assertEqual(lookup_subject(path,"宇宙")[0].statement,first[0].statement)
    def test_explicit_id_preserved(self):
        r=self.row()
        r["proposition_id"]="stable-original-id"
        self.assertEqual(normalize_record(r).proposition_id,"stable-original-id")
    def test_bridge_ready_after_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"memory.jsonl"
            path.write_text(json.dumps(self.row(),ensure_ascii=False)+"\n",encoding="utf-8")
            report=bridge_records(load_memory(path),"宇宙")
            self.assertEqual(report.status,"READY")
            self.assertEqual(len(report.evidence),1)
    def test_empty_source_no_bridge(self):
        r=self.row()
        r["source"]=""
        report=bridge_records([normalize_record(r)],"宇宙")
        self.assertEqual(report.status,"MISSING_SOURCE")
    def test_duplicate_id_conflict_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"memory.jsonl"
            a=self.row()
            b=self.row("別の記述。")
            a["proposition_id"]=b["proposition_id"]="same-id"
            path.write_text("\n".join(json.dumps(v,ensure_ascii=False) for v in (a,b))+"\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                load_memory(path)

if __name__=="__main__":
    unittest.main()
