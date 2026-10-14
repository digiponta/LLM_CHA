import json
import tempfile
import unittest
from pathlib import Path
from conversation_resource_memory_v042866 import new_conversation,append_turn,close_session,write_json_atomic
from sleep_eviction_integration_v042870 import integrate

class SleepEvictionIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  root=Path(self.temp.name)
  self.conversations=root/"conversations";self.conversations.mkdir()
  self.artifacts=root/"artifacts";self.artifacts.mkdir()
  self.source=self.conversations/"synthetic.conversation.json"
  self.candidates=self.artifacts/"candidates.json"
  self.propositions=self.artifacts/"propositions.json"
  self.evidence=self.artifacts/"evidence.json"
  self.audit=self.artifacts/"audit.json"
 def make(self,lines=("私は音楽が好き",)):
  m=new_conversation("synthetic-session")
  for speaker,text in lines:append_turn(m,speaker,text)
  close_session(m);write_json_atomic(m,self.source)
 def call(self,**kwargs):
  return integrate(self.source,self.candidates,self.propositions,self.evidence,self.audit,**kwargs)
 def test_dry_run_no_mutation(self):
  self.make((("A","私は音楽が好き"),))
  r=self.call()
  self.assertEqual(r["mode"],"DRY_RUN")
  self.assertTrue(self.source.exists())
  self.assertFalse(self.candidates.exists())
 def test_complete_coverage_deletion(self):
  self.make((("A","私は音楽が好き"),("B","私は映画が好き")))
  r=self.call(apply=True,confirm_delete=True)
  self.assertTrue(r["deleted"]);self.assertFalse(self.source.exists())
  self.assertTrue(self.propositions.exists());self.assertTrue(self.evidence.exists())
 def test_uncovered_turn_protected(self):
  self.make((("A","私は音楽が好き"),("B","こんにちは")))
  r=self.call(apply=True,confirm_delete=True)
  self.assertEqual(r["reason"],"UNCOVERED_TURNS")
  self.assertTrue(self.source.exists())
 def test_zero_candidates_protected(self):
  self.make((("A","こんにちは"),))
  r=self.call(apply=True,confirm_delete=True)
  self.assertFalse(r["deleted"]);self.assertTrue(self.source.exists())
 def test_wrong_confirmation(self):
  self.make((("A","私は音楽が好き"),))
  with self.assertRaises(ValueError):self.call(apply=True)
 def test_artifact_mismatch(self):
  self.make((("A","私は音楽が好き"),))
  self.candidates.write_text('{"bad":true}',encoding="utf-8")
  with self.assertRaises(ValueError):self.call(apply=True,confirm_delete=True)
  self.assertTrue(self.source.exists())
 def test_evidence_preserves_source(self):
  self.make((("B","私は音楽が好き"),))
  self.call(apply=True,confirm_delete=True)
  e=json.loads(self.evidence.read_text(encoding="utf-8"))
  self.assertEqual(e["entries"][0]["source_text"],"私は音楽が好き")
  self.assertEqual(e["entries"][0]["speaker"],"B")
 def test_recovery_after_partial_processing(self):
  self.make((("A","私は音楽が好き"),("B","こんにちは")))
  self.call(apply=True,confirm_delete=True)
  again=self.call(apply=True,confirm_delete=True)
  self.assertFalse(again["deleted"])
  self.assertTrue(self.source.exists())
 def test_cross_session_artifact_protected(self):
  self.make((("A","私は音楽が好き"),))
  self.call(apply=True,confirm_delete=True)
  # Already removed: second operation cannot silently reuse source.
  with self.assertRaises(FileNotFoundError):self.call(apply=True,confirm_delete=True)
 def test_paths_isolation(self):
  self.make((("A","私は音楽が好き"),))
  with self.assertRaises(ValueError):
   integrate(self.source,self.source,self.propositions,self.evidence,self.audit)
if __name__=="__main__":unittest.main()
