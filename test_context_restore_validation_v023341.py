import json
import unittest
from longterm_context_v02340 import ContextCheckpoint
from proposition_truth_v0233827 import TruthOverlay, proposition_id
from context_restore_validation_v023341 import (
    CurrentProposition, CurrentSubject, validate_restored_context,
)

TOPIC = "宇宙"
P = CurrentProposition("宇宙は広大", "test-corpus")
PID = proposition_id(TOPIC, P.statement, P.provenance)

def snapshot(*ids):
    c = ContextCheckpoint()
    for pid in ids:
        c.remember(TOPIC, pid)
    return c.export()

def catalog(state="TRUE", allowed=True, props=(P,)):
    return {TOPIC: CurrentSubject(props, state, allowed)}

class RestoreValidationTests(unittest.TestCase):
    def test_valid_retained(self):
        r=validate_restored_context(snapshot(PID), catalog(), TruthOverlay())
        self.assertEqual((r.retained,r.rejected),(1,0))
        self.assertEqual(r.context.active_topic,TOPIC)

    def test_missing_subject(self):
        r=validate_restored_context(snapshot(PID),{},TruthOverlay())
        self.assertEqual(r.rejected,1)
        self.assertIsNone(r.context.active_topic)

    def test_corpus_modified(self):
        changed=CurrentProposition("宇宙は広大", "new-provenance")
        r=validate_restored_context(snapshot(PID),catalog(props=(changed,)),TruthOverlay())
        self.assertEqual(r.retained,0)

    def test_missing_proposition(self):
        r=validate_restored_context(snapshot(PID),catalog(props=()),TruthOverlay())
        self.assertEqual(r.rejected,1)

    def test_blocked_subject(self):
        r=validate_restored_context(snapshot(PID),catalog("FALSE",False),TruthOverlay())
        self.assertEqual(r.retained,0)

    def test_true_overlay_cannot_override_subject(self):
        o=TruthOverlay()
        o.rows[PID]=("TRUE","review")
        r=validate_restored_context(snapshot(PID),catalog("FALSE",False),o)
        self.assertEqual(r.retained,0)

    def test_blocked_overlay(self):
        for state in ("FALSE","OUTDATED","CONTESTED"):
            with self.subTest(state=state):
                o=TruthOverlay()
                o.rows[PID]=(state,"review")
                r=validate_restored_context(snapshot(PID),catalog(),o)
                self.assertEqual(r.retained,0)

    def test_mixed_ids_filter(self):
        r=validate_restored_context(snapshot(PID,"deadbeef"),catalog(),TruthOverlay())
        self.assertEqual((r.retained,r.rejected),(1,1))
        self.assertEqual(r.context.topics[TOPIC],[PID])

    def test_unverified_permitted_only_if_subject_permits(self):
        r=validate_restored_context(snapshot(PID),catalog("UNVERIFIED",True),TruthOverlay())
        self.assertEqual(r.retained,1)
        r=validate_restored_context(snapshot(PID),catalog("UNVERIFIED",False),TruthOverlay())
        self.assertEqual(r.retained,0)

    def test_malformed_schema_fails(self):
        with self.assertRaises(ValueError):
            validate_restored_context('{"schema":"old","topics":{}}',catalog(),TruthOverlay())

    def test_duplicate_authoritative_id_rejected(self):
        r=validate_restored_context(snapshot(PID),catalog(props=(P,P)),TruthOverlay())
        self.assertEqual(r.retained,0)

if __name__ == "__main__":
    unittest.main()
