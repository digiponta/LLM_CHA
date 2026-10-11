import json,tempfile,unittest
from pathlib import Path
from multilayer_semantic_audit_v023363 import audit_layers

class MultiLayerAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.atomic=self.root/"atomic.jsonl";self.subject=self.root/"subject.jsonl"
        self.typed=self.root/"typed.jsonl";self.unified=self.root/"unified.jsonl"
        def write(path,rows):
            path.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf8")
        write(self.atomic,[{"subject":"A","value":"Bを含む"},{"subject":"B","value":"Cを含む"}])
        write(self.subject,[{"subject":"A","value":"Bを含む","statement":"AはBを含むである。"},
                            {"subject":"B","value":"Cを含む","statement":"BはCを含むである。"}])
        write(self.typed,[{"subject":"A","value":"Bを含む","statement":"AはBを含むである。","predicate_type":"relation"},
                          {"subject":"B","value":"Cを含む","statement":"BはCを含むである。","predicate_type":"relation"}])
        write(self.unified,[{"concept":"A","assistant":"AはBを含む","source":"atomic-proposition"},
                            {"concept":"B","assistant":"BはCを含む","source":"atomic-proposition"}])
    def test_duplicates_are_not_evidence(self):
        r=audit_layers(self.atomic,self.subject,self.typed,self.unified)
        self.assertEqual(r["unique_propositions"],2)
        self.assertEqual(r["canonical_propositions"],2)
        self.assertEqual(r["orphaned_derived"],0)
        self.assertEqual(r["independent_evidence_count"],0)
        self.assertEqual(len(r["rows"][0]["layers"]),3)
    def test_subject_filter(self):
        r=audit_layers(self.atomic,self.subject,self.typed,self.unified,"A")
        self.assertEqual(r["unique_propositions"],1)
        self.assertEqual(r["rows"][0]["subject"],"A")
    def test_detect_orphan(self):
        with self.subject.open("a",encoding="utf8") as f:
            f.write(json.dumps({"subject":"A","value":"Dを含む","statement":"AはDを含むである。"},ensure_ascii=False)+"\n")
        r=audit_layers(self.atomic,self.subject,self.typed,self.unified)
        self.assertEqual(r["orphaned_derived"],1)
        self.assertFalse(next(x for x in r["rows"] if x["value"]=="Dを含む")["canonical"])
    def test_unified_not_proof(self):
        r=audit_layers(self.atomic,self.subject,self.typed,self.unified)
        self.assertEqual(r["unified_concepts_matched"],2)
        self.assertEqual(r["independent_evidence_count"],0)

if __name__=="__main__":unittest.main()
