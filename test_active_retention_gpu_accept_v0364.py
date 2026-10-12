import unittest
from active_retention_gpu_accept_v0364 import TOPICS,COMMANDS,segment,diagnostic

class ActiveGpuHarnessTests(unittest.TestCase):
    def test_topic_churn_exceeds_eight(self):
        self.assertGreater(len(TOPICS),8)
    def test_revisit_after_churn(self):
        self.assertIn("宇宙の話に戻って",COMMANDS)
    def test_reset_sequence(self):
        self.assertLess(COMMANDS.index("/reset"),COMMANDS.index("それについて"))
    def test_segment(self):
        text="You> 宇宙とは\nAI> 回答\nYou> GPUとは\nAI> GPU回答\n"
        self.assertIn("AI> 回答",segment(text,"宇宙とは"))
        self.assertNotIn("GPU回答",segment(text,"宇宙とは"))
    def test_missing_segment(self):
        self.assertIsNone(segment("text","宇宙とは"))
    def test_diagnostic(self):
        out='You> /retention-stats\n{"mode": "active", "topics": []}\nYou> /exit'
        self.assertEqual(diagnostic(out)["mode"],"active")
    def test_missing_diagnostic(self):
        self.assertIsNone(diagnostic("You> /retention-stats\n[disabled]\n"))
    def test_has_stats_after_reset(self):
        self.assertEqual(COMMANDS.count("/retention-stats"),2)

if __name__=="__main__":unittest.main()
