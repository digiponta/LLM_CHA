import unittest
from prepare_prefix_recovery_v02304 import build,classify
from evaluate_prefix_recovery_v02304 import score

class RecoveryTests(unittest.TestCase):
    def test_modes(self):
        rows=build()
        self.assertEqual(len(rows),12)
        self.assertEqual(sum(x["mode"]=="continue" for x in rows),6)
        self.assertEqual(sum(x["mode"]=="restart" for x in rows),6)
    def test_routing(self):
        self.assertEqual(classify("カレー","カレーは、"),"continue")
        self.assertEqual(classify("カレー","長門有希。"),"restart")
    def test_no_wrong_prefix_append(self):
        for row in build():
            if row["mode"]=="restart":
                self.assertFalse(row["assistant"].startswith(row["prefix"]))
                self.assertIn("[RESTART]",row["user"])
            else:
                self.assertIn("[CONTINUE]",row["user"])
    def test_no_holdout_topics(self):
        from prepare_topic_grounded_v02290 import HOLDOUT
        rows=build()
        self.assertTrue(all(r["topic"] not in HOLDOUT for r in rows))
    def test_score_not_strict_exact(self):
        s=score("写真撮影","continue","光の向きを変えると印象が変わる。")
        self.assertTrue(s["lexical_topic"])
        self.assertFalse(s["topic_exact"])
    def test_restart_exact(self):
        self.assertTrue(score("カレー","restart","カレーには香辛料を使う。")["restart_topic_mention"])
if __name__=="__main__":unittest.main()
