import unittest
from topic_answer_context_v013588226 import TopicAnswerContext
class Tests(unittest.TestCase):
 def test_return(self):
  c=TopicAnswerContext();c.note_question("宇宙とは");c.record("宇宙とは","宇宙は膨張している。")
  c.note_question("CPU");c.record("CPU","CPUは中央処理装置。")
  state,topic,answer=c.navigate("宇宙の話に戻って")
  self.assertEqual(state,"RETURNED")
  self.assertEqual(topic,"宇宙")
  self.assertIn("膨張",answer)
 def test_more_after_return(self):
  c=TopicAnswerContext();c.record("宇宙とは","宇宙は膨張している。")
  c.record("CPU","CPUは演算装置。")
  c.navigate("宇宙の話に戻って")
  state,topic,_=c.navigate("もう少し詳しく")
  self.assertEqual((state,topic),("ELABORATE","宇宙"))
  self.assertIn("宇宙",c.elaborate(topic))
 def test_no_answer(self):
  c=TopicAnswerContext()
  self.assertEqual(c.navigate("もう少し詳しく")[0],"NO_CONTEXT")
  self.assertEqual(c.navigate("宇宙の話に戻って")[0],"TOPIC_NOT_RECORDED")
 def test_no_bad_answer_history(self):
  c=TopicAnswerContext();c.note_question("宇宙とは")
  self.assertFalse(c.record("宇宙とは","未学習です"))
  self.assertFalse(c.record("宇宙とは","無用反面、知能。"))
  self.assertFalse(c.history)
 def test_bounded(self):
  c=TopicAnswerContext(capacity=2)
  for n in "ABC":c.record(n,n+"について説明")
  self.assertEqual(list(c.history),["B","C"])
 def test_not_semantic_promotion(self):
  c=TopicAnswerContext();c.record("宇宙とは","独自の宇宙論仮説。")
  self.assertIn("検証",c.navigate("宇宙の話に戻って")[2])
 def test_unrelated_query(self):
  self.assertIsNone(TopicAnswerContext().navigate("量子力学とは"))
if __name__=="__main__":unittest.main()
