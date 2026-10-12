import tempfile
from pathlib import Path
import json
import unittest
from proposition_truth_v0233827 import TruthOverlay, proposition_id

class PropositionTruthTests(unittest.TestCase):
    def test_stable_identifier(self):
        a=proposition_id("宇宙","宇宙は膨張する","corpus")
        self.assertEqual(a,proposition_id("宇宙","宇宙は膨張する","corpus"))
        self.assertNotEqual(a,proposition_id("宇宙","宇宙は膨張する","other"))

    def test_inherit(self):
        d=TruthOverlay().decide("宇宙","A","corpus","UNVERIFIED",True)
        self.assertEqual(d.state,"UNVERIFIED")
        self.assertTrue(d.allowed)

    def test_subject_block_cannot_be_overridden(self):
        pid=proposition_id("宇宙","A","corpus")
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"truth.jsonl"
            p.write_text(json.dumps({"proposition_id":pid,"truth_state":"TRUE"}),encoding="utf-8")
            d=TruthOverlay(str(p)).decide("宇宙","A","corpus","FALSE",False)
            self.assertFalse(d.allowed)

    def test_false_proposition_blocked(self):
        pid=proposition_id("宇宙","A","corpus")
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"truth.jsonl"
            p.write_text(json.dumps({"proposition_id":pid,"truth_state":"FALSE"}),encoding="utf-8")
            self.assertFalse(TruthOverlay(str(p)).decide("宇宙","A","corpus","UNVERIFIED",True).allowed)

    def test_overlay_does_not_write(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"truth.jsonl"
            p.write_text("",encoding="utf-8")
            before=p.read_bytes()
            TruthOverlay(str(p)).decide("a","b","c","TRUE",True)
            self.assertEqual(before,p.read_bytes())

    def test_invalid_overlay_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"truth.jsonl"
            p.write_text('{"proposition_id":"bad","truth_state":"TRUE"}',encoding="utf-8")
            with self.assertRaises(ValueError): TruthOverlay(str(p))

if __name__=="__main__": unittest.main()
