import json,tempfile,unittest
from pathlib import Path
from runtime_reference_integration_v023352 import SessionReferenceStore,RuntimeReferenceBridge
from verified_reference_concept_v023356 import VerifiedConceptMapping
from session_multi_evidence_bridge_v023362 import MultiEvidenceBridge

class SessionMultiEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.refs=SessionReferenceStore(root/"refs.sqlite3")
        self.runtime=RuntimeReferenceBridge(self.refs)
        self.maps=VerifiedConceptMapping(root/"maps.sqlite3")
        self.propositions=root/"semantic_propositions.jsonl"
        self.manifest=root/"manifest.json"
        self.propositions.write_text(
            '{"subject":"A","value":"Bを含む"}\n'
            '{"subject":"B","value":"Cを含む"}\n'
            '{"subject":"A","value":"Cを含まない"}\n',encoding="utf-8")
        self.entries=[
            {"statement":"AはBを含む","truth":"TRUE","source":"local reviewed test","evidence_id":"e1"},
            {"statement":"BはCを含む","truth":"TRUE","source":"local reviewed test","evidence_id":"e2"}]
        self.save()
        self.bridge=MultiEvidenceBridge(self.refs,self.maps,self.propositions,self.manifest)
    def save(self):
        self.manifest.write_text(json.dumps(
            {"schema":1,"transitive_relations":["includes"],"evidence":self.entries},
            ensure_ascii=False),encoding="utf8")
    def approve(self):
        for t in ("昨日の実験の続きをやって","cursor","はい"):
            self.runtime.receive(t,"A")
        token=self.maps.propose("A","cursor","A","local-user-confirmed-mapping")
        self.assertTrue(self.maps.approve("A",token))
    def test_positive_path(self):
        self.approve()
        result=self.bridge.lookup("A","AはCを含む")
        self.assertEqual(result["status"],"supported",result)
        self.assertEqual(result["path"],["e1","e2"])
    def test_no_session_reference(self):
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"no_approved_reference")
    def test_missing_mapping(self):
        self.runtime.receive("昨日の実験の続きをやって","A")
        self.runtime.receive("cursor","A")
        self.runtime.receive("はい","A")
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"no_approved_mapping")
    def test_wrong_context(self):
        self.approve()
        self.assertEqual(self.bridge.lookup("B","AはCを含む")["reason"],"no_approved_reference")
    def test_unmapped_subject(self):
        self.approve()
        self.assertEqual(self.bridge.lookup("A","BはCを含む")["reason"],"mapped_subject_mismatch")
    def test_manifest_unverified(self):
        self.approve();self.entries[1]["truth"]="UNVERIFIED";self.save()
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"unvalidated_manifest_entry")
    def test_manifest_absent(self):
        self.approve();self.manifest.unlink()
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"no_evidence_manifest")
    def test_missing_proposition(self):
        self.approve()
        self.propositions.write_text('{"subject":"A","value":"Bを含む"}\n',encoding="utf8")
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"manifest_statement_not_in_semantic_memory")
    def test_duplicate_evidence(self):
        self.approve();self.entries[1]["evidence_id"]="e1";self.save()
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"duplicate_or_missing_evidence_id")
    def test_direct_counterevidence(self):
        self.approve()
        self.entries.append({"statement":"AはCを含まない","truth":"TRUE",
                             "source":"local reviewed test","evidence_id":"e3"});self.save()
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"explicit_counterevidence")
    def test_no_implicit_transitivity(self):
        self.approve()
        self.manifest.write_text(json.dumps({"schema":1,"transitive_relations":[],
                                              "evidence":self.entries}),encoding="utf8")
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"invalid_policy_manifest")
    def test_invalidated_mapping(self):
        self.approve();self.maps.invalidate("A","cursor")
        self.assertEqual(self.bridge.lookup("A","AはCを含む")["reason"],"no_approved_mapping")

if __name__=="__main__":unittest.main()
