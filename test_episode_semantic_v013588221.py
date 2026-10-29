import unittest
from episode_semantic_v013588221 import normalize_observation
from episodic_context_v013588220 import EpisodeContext

class SemanticEpisodeTests(unittest.TestCase):
 def test_smell_and_bitter(self):
  c=EpisodeContext()
  c.start("スターバックス","スターバックス ラテ","飲んだ")
  c.observe("香りは良かったけれど、少し苦かった","スターバックス")
  self.assertEqual(len(c.active.observations),2)
  facts=[fact for obs in c.active.observations for fact in obs["semantic"]]
  self.assertTrue(any(x["attribute"]=="香り" and x["polarity"]=="positive" for x in facts))
  self.assertTrue(any(x["attribute"]=="苦味" and x["value"]=="少し苦い" for x in facts))
  self.assertTrue(all(obs["original_utterance"]=="香りは良かったけれど、少し苦かった" for obs in c.active.observations))
 def test_satisfaction(self):
  facts=normalize_observation("満足")
  self.assertTrue(any(x["attribute"]=="満足" and x["polarity"]=="positive" for x in facts))
 def test_preference(self):
  facts=normalize_observation("カフェアメリカーノも好き")
  self.assertTrue(any(x["attribute"]=="好み" for x in facts))
 def test_no_made_up(self):
  self.assertEqual(normalize_observation("何も書いていない"),[])
 def test_topic_isolation(self):
  c=EpisodeContext();c.start("A","ラテ","飲んだ")
  self.assertEqual(c.observe("少し苦かった","B"),[])
if __name__=="__main__":unittest.main()
