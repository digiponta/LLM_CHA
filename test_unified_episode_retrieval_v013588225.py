import tempfile
import unittest
from pathlib import Path
from episodic_context_v013588220 import EpisodeContext
from episodic_memory_gate_v013588223 import EpisodicMemoryGate
from unified_episode_retrieval_v013588225 import UnifiedEpisodeRetriever

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.ctx=EpisodeContext()
  self.gate=EpisodicMemoryGate(Path(self.tmp.name)/"approved.json")
  self.reader=UnifiedEpisodeRetriever(self.ctx,self.gate)
 def make(self,subject,action,approved=False,satisfied=False):
  e=self.ctx.start("スターバックス",subject,action)
  if satisfied:self.ctx.observe("満足","スターバックス")
  if approved:
   item=self.gate.stage(e);self.gate.approve(item["episode_id"])
  return e
 def test_session_only(self):
  self.make("カフェアメリカーノ","好み")
  x=self.reader.answer("好きな商品は？")
  self.assertIn("カフェアメリカーノ",x)
  self.assertIn("今回の会話",x)
 def test_approved_only_after_restart(self):
  self.make("黒耳","飲んだ",True,True)
  x=UnifiedEpisodeRetriever(EpisodeContext(),EpisodicMemoryGate(self.gate.path)).answer("何を飲んだ？")
  self.assertIn("黒耳",x)
  self.assertIn("承認済み",x)
 def test_dedup_approved_snapshot(self):
  self.make("黒耳","飲んだ",True,True)
  x=self.reader.answer("何を飲んだ？")
  self.assertEqual(x.count("・黒耳"),1)
 def test_approved_and_session(self):
  self.make("黒耳","飲んだ",True)
  self.make("ラテ","飲んだ")
  x=self.reader.answer("何を飲んだ？")
  self.assertIn("黒耳",x);self.assertIn("ラテ",x)
  self.assertIn("今回の会話",x);self.assertIn("承認済み",x)
 def test_preference_not_drinking(self):
  self.make("アメリカーノ","好み")
  self.assertNotIn("アメリカーノ",self.reader.answer("何を飲んだ？"))
 def test_followup_and_revoke(self):
  self.make("黒耳","飲んだ",True,True)
  new_reader=UnifiedEpisodeRetriever(EpisodeContext(),EpisodicMemoryGate(self.gate.path))
  new_reader.answer("何を飲んだ？")
  self.assertIn("満足",new_reader.answer("その時は満足した？"))
  id=self.gate.list_approved()[0]["episode_id"]
  self.gate.revoke(id)
  self.assertIn("検索対象にありません",new_reader.answer("その時は満足した？"))
 def test_multiple_followup_ambiguous(self):
  self.make("黒耳","飲んだ")
  self.make("ラテ","飲んだ")
  self.reader.answer("何を飲んだ？")
  self.assertIn("特定できません",self.reader.answer("その時は満足した？"))
 def test_unrelated_passthrough(self):
  self.assertIsNone(self.reader.answer("量子力学とは？"))
if __name__=="__main__":unittest.main()
