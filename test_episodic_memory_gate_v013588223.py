import tempfile
import unittest
from pathlib import Path
from episodic_context_v013588220 import EpisodeContext
from episodic_memory_gate_v013588223 import EpisodicMemoryGate, SCHEMA

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"approved.json"
        self.gate=EpisodicMemoryGate(self.path)
        ctx=EpisodeContext()
        self.episode=ctx.start("スターバックス","カフェアメリカーノ","好み")
        ctx.observe("カフェアメリカーノも好き","スターバックス")
    def test_stage_is_not_persisted(self):
        item=self.gate.stage(self.episode)
        self.assertEqual(item["schema"],SCHEMA)
        self.assertEqual(item["approval"],"PENDING")
        self.assertFalse(self.path.exists())
    def test_explicit_approval(self):
        item=self.gate.stage(self.episode)
        self.gate.approve(item["episode_id"])
        self.assertEqual(len(self.gate.list_approved()),1)
        self.assertEqual(self.gate.list_approved()[0]["approval"],"APPROVED")
    def test_reject(self):
        item=self.gate.stage(self.episode)
        self.gate.reject(item["episode_id"])
        self.assertFalse(self.path.exists())
        with self.assertRaises(KeyError):self.gate.approve(item["episode_id"])
    def test_revoke(self):
        item=self.gate.stage(self.episode)
        self.gate.approve(item["episode_id"])
        self.gate.revoke(item["episode_id"])
        self.assertEqual(self.gate.list_approved(),[])
    def test_provenance(self):
        item=self.gate.stage(self.episode)
        self.assertEqual(item["provenance"],"USER_SELF_REPORTED")
        self.assertTrue(all(o["provenance"]=="USER_SELF_REPORTED" for o in item["observations"]))
    def test_unknown_id(self):
        with self.assertRaises(KeyError):self.gate.approve("missing")
    def test_original_and_semantic(self):
        item=self.gate.stage(self.episode)
        self.assertIn("original_utterance",item["observations"][0])
        self.assertIn("semantic",item["observations"][0])
if __name__=="__main__":unittest.main()
