import unittest
from active_retention_gpu_accept_v0364 import TOPICS,COMMANDS,segment,diagnostic

class ActiveGpuHarnessTests(unittest.TestCase):
    def test_topic_churn_exceeds_eight(self):
        self.assertGreater(len(TOPICS),8)
    def test_revisit_after_churn(self):
        self.assertIn("宇宙の話に戻って",COMMANDS)
    def test_reset_sequence(self):
        self.assertLess(COMMANDS.index("/reset"),COMMANDS.index("それについて"))
    @staticmethod
    def fake_output(replacements=None):
        replacements=replacements or {}
        return "\n".join("You> "+replacements.get(i,"[0 generated probe tokens]")
                         for i in range(len(COMMANDS)))+"\n"

    def test_segment(self):
        out=self.fake_output({0:"AI> 回答",1:"AI> GPU回答"})
        self.assertIn("AI> 回答",segment(out,"宇宙とは"))
        self.assertNotIn("GPU回答",segment(out,"宇宙とは"))
    def test_missing_segment(self):
        self.assertIsNone(segment("text","宇宙とは"))
    def test_diagnostic(self):
        out=self.fake_output({COMMANDS.index("/retention-stats"):
                             '{"mode": "active", "topics": []}'})
        self.assertEqual(diagnostic(out)["mode"],"active")
    def test_missing_diagnostic(self):
        self.assertIsNone(diagnostic(self.fake_output()))
    def test_reset_diagnostic_is_second_occurrence(self):
        indices=[i for i,c in enumerate(COMMANDS) if c=="/retention-stats"]
        out=self.fake_output({indices[0]:'{"mode":"active","topics":["宇宙"]}',
                              indices[1]:'{"mode":"active","topics":[]}'})
        self.assertEqual(diagnostic(out,0)["topics"],["宇宙"])
        self.assertEqual(diagnostic(out,1)["topics"],[])

    def test_has_stats_after_reset(self):
        self.assertEqual(COMMANDS.count("/retention-stats"),2)

if __name__=="__main__":unittest.main()
