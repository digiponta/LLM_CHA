import json
import tempfile
import unittest
from pathlib import Path
from mixed_state_e2e_v0233829 import MixedStateEvaluator
from proposition_truth_v0233827 import TruthOverlay, proposition_id

class MixedStateE2ETests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        provenance="fixture:mixed-state"
        self.rows=[("命題A","TRUE"),("命題B","FALSE"),("命題C","UNVERIFIED"),
                   ("命題D","OUTDATED"),("命題E","CONTESTED")]
        self.path=Path(self.dir.name)/"overlay.jsonl"
        self.path.write_text("".join(json.dumps({
            "proposition_id":proposition_id("評価用話題",t,provenance),
            "truth_state":state,"provenance":provenance
        },ensure_ascii=False)+"\n" for t,state in self.rows),encoding="utf-8")
        self.corpus={"評価用話題":(" / ".join(t for t,_ in self.rows),
                      provenance,"UNVERIFIED")}
        self.e=MixedStateEvaluator(self.corpus,TruthOverlay(str(self.path)))

    def test_true_first(self):
        r=self.e.turn("評価用話題について教えて")
        self.assertEqual((r.status,r.proposition,r.truth_state),
                         ("DISPLAY","命題A","TRUE"))

    def test_blocked_false_outdated_contested(self):
        self.e.turn("評価用話題について教えて")
        r=self.e.turn("もう少し詳しく")
        self.assertEqual((r.status,r.proposition,r.truth_state),
                         ("DISPLAY","命題C","UNVERIFIED"))
        self.assertEqual(self.e.turn("もう少し詳しく").status,"EXHAUSTED")

    def test_no_repeat(self):
        output=[self.e.turn("評価用話題について教えて")]
        output.extend(self.e.turn("もう少し詳しく") for _ in range(3))
        self.assertEqual([o.proposition for o in output if o.status=="DISPLAY"],
                         ["命題A","命題C"])

    def test_topic_reset(self):
        self.e.turn("評価用話題について教えて")
        self.assertEqual(self.e.turn("/reset").status,"RESET")
        self.assertEqual(self.e.turn("もう少し詳しく").status,"NO_TOPIC")
        self.assertEqual(self.e.turn("評価用話題について教えて").proposition,"命題A")

    def test_subject_false_blocks_true_overlay(self):
        self.corpus["評価用話題"]=(self.corpus["評価用話題"][0],
                                "fixture:mixed-state","FALSE")
        self.assertEqual(self.e.turn("評価用話題について教えて").status,
                         "BLOCK_SUBJECT")

    def test_independent_topics(self):
        self.corpus["別話題"]=("別命題","fixture:other","UNVERIFIED")
        self.e.turn("評価用話題について教えて")
        self.assertEqual(self.e.turn("別話題について教えて").proposition,"別命題")
        self.assertEqual(self.e.turn("評価用話題の話に戻って").proposition,"命題C")

    def test_fixture_not_modified(self):
        original=self.path.read_bytes()
        self.e.turn("評価用話題について教えて")
        self.e.turn("もう少し詳しく")
        self.assertEqual(self.path.read_bytes(),original)

    def test_stable_proposition_id(self):
        r=self.e.turn("評価用話題について教えて")
        self.assertEqual(r.proposition_id,
                         proposition_id("評価用話題","命題A","fixture:mixed-state"))

if __name__=="__main__":
    unittest.main()
