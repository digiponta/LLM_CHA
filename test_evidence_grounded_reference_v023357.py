import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as Obj
from unittest.mock import Mock
from runtime_reference_integration_v023352 import SessionReferenceStore,RuntimeReferenceBridge
from verified_reference_concept_v023356 import VerifiedConceptMapping
from evidence_grounded_reference_v023357 import evidence_gate,EvidenceGroundedReferenceBridge

def result(truth="TRUE",state="KNOWN",action="ANSWER",source="validated_index",
           evidence="user-reviewed document",answer="検証対象の回答"):
    return Obj(truth_state=truth,state=state,action=action,answer=answer,
               provenance=Obj(source=source,evidence=evidence,origin=""))

class EvidenceGateTests(unittest.TestCase):
    def test_allow_metadata_complete(self):
        self.assertEqual(evidence_gate(result()),(True,"supported_by_metadata"))
    def test_unknown_and_raw_are_blocked(self):
        for state in ("UNKNOWN","RAW_CORPUS_ONLY","CONTESTED","OUTDATED"):
            with self.subTest(state=state):
                self.assertFalse(evidence_gate(result(state=state))[0])
    def test_truth_not_true(self):
        for truth in ("UNVERIFIED","FALSE","CONTESTED","OUTDATED"):
            with self.subTest(truth=truth):
                self.assertFalse(evidence_gate(result(truth=truth))[0])
    def test_source_and_dispatch(self):
        for case in (result(source="none"),result(evidence=""),result(action="BLOCK"),
                     result(action="UNKNOWN"),result(answer="")):
            self.assertFalse(evidence_gate(case)[0])
    def test_missing_provenance(self):
        r=result();r.provenance=None
        self.assertFalse(evidence_gate(r)[0])
    def test_end_to_end_approved_mapping(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            refs=SessionReferenceStore(path/"refs.sqlite3")
            runtime=RuntimeReferenceBridge(refs)
            for utterance in ("昨日の実験の続きをやって","cursor","はい"):
                runtime.receive(utterance,"A")
            maps=VerifiedConceptMapping(path/"maps.sqlite3")
            sem=Mock();sem.resolve.return_value=result()
            bridge=EvidenceGroundedReferenceBridge(refs,maps,sem)
            self.assertEqual(bridge.lookup("A")["status"],"no_approved_mapping")
            candidate=maps.propose("A","cursor","数学","explicit-user")
            self.assertEqual(bridge.lookup("A")["status"],"no_approved_mapping")
            maps.approve("A",candidate)
            good=bridge.lookup("A")
            self.assertEqual(good["status"],"evidence_allowed")
            sem.resolve.assert_called_once_with("数学とは")
            self.assertEqual(good["answer"],"検証対象の回答")
            self.assertEqual(bridge.lookup("B")["status"],"no_approved_reference")
            sem.resolve.return_value=result(truth="UNVERIFIED")
            blocked=bridge.lookup("A")
            self.assertEqual(blocked["status"],"evidence_blocked")
            self.assertEqual(blocked["answer"],"")
if __name__=="__main__":unittest.main()
