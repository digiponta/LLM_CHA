import tempfile
import unittest
from pathlib import Path
from episodic_context_v013588220 import EpisodeContext
from episodic_memory_gate_v013588223 import EpisodicMemoryGate
from approved_episode_retrieval_v013588224 import ApprovedEpisodeRetriever

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/"approved.json"
  self.gate=EpisodicMemoryGate(self.path)
  self.ctx=EpisodeContext()
 def approved(self,name,action,with_satisfaction=False):
  e=self.ctx.start("スターバックス",name,action)
  if with_satisfaction:self.ctx.observe("満足","スターバックス")
  item=self.gate.stage(e)
  self.gate.approve(item["episode_id"])
  return item["episode_id"]
 def test_restart_read(self):
  self.approved("黒耳","飲んだ",True)
  reader=ApprovedEpisodeRetriever(EpisodicMemoryGate(self.path))
  self.assertIn("黒耳",reader.answer("以前、何を飲んだ？"))
 def test_preference_not_drink(self):
  self.approved("カフェアメリカーノ","好み")
  result=ApprovedEpisodeRetriever(EpisodicMemoryGate(self.path)).answer("以前、何を飲んだ？")
  self.assertIn("ありません",result)
 def test_followup(self):
  self.approved("黒耳","飲んだ",True)
  reader=ApprovedEpisodeRetriever(EpisodicMemoryGate(self.path))
  reader.answer("以前、何を飲んだ？")
  self.assertIn("満足した",reader.answer("その時は満足した？"))
 def test_followup_without_reference(self):
  self.approved("黒耳","飲んだ",True)
  reader=ApprovedEpisodeRetriever(EpisodicMemoryGate(self.path))
  self.assertIn("特定できません",reader.answer("その時は満足した？"))
 def test_no_inferred_satisfaction(self):
  self.approved("黒耳","飲んだ")
  reader=ApprovedEpisodeRetriever(EpisodicMemoryGate(self.path))
  reader.answer("以前、何を飲んだ？")
  self.assertIn("確認できません",reader.answer("その時は満足した？"))
 def test_revoke_visibility(self):
  id=self.approved("黒耳","飲んだ")
  self.gate.revoke(id)
  self.assertIn("ありません",ApprovedEpisodeRetriever(EpisodicMemoryGate(self.path)).answer("以前、何を飲んだ？"))
 def test_ignored_unapproved(self):
  e=self.ctx.start("スターバックス","ラテ","飲んだ")
  self.gate.stage(e)
  self.assertIn("ありません",ApprovedEpisodeRetriever(self.gate).answer("以前、何を飲んだ？"))
 def test_generic_question_passthrough(self):
  self.assertIsNone(ApprovedEpisodeRetriever(self.gate).answer("量子力学とは？"))
if __name__=="__main__":unittest.main()
