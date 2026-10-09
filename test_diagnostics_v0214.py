import unittest
from context_ablation_v0214 import swap_history
from generation_quality_v0214 import metrics

class DiagnosticV0214Tests(unittest.TestCase):
    def test_shuffled_history_keeps_target_utterance(self):
        original="人: 本を読みました\nAI: どんな本？\n人: SFです"
        other="人: 散歩しました\nAI: どこに？\n人: 公園です"
        self.assertEqual(swap_history(original,other),"人: 散歩しました\nAI: どこに？\n人: SFです")
    def test_no_history_not_shuffled(self):
        self.assertIsNone(swap_history("人: SFです","人: 公園です"))
    def test_generation_proxy_metrics(self):
        rows=[{"prompt":"人: SFです","generated":"そう。"},
              {"prompt":"人: SFです","generated":"SFは宇宙を描く作品が多いです。"}]
        m=metrics(rows)
        self.assertEqual(m["count"],2)
        self.assertEqual(m["generic_fraction"],.5)
        self.assertEqual(m["distinct_response_fraction"],1.)
if __name__=="__main__":unittest.main()
