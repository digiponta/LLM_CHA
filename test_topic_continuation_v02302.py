import unittest
from prepare_topic_continuation_v02302 import build,validate
from prepare_topic_grounded_v02290 import TRAIN,HOLDOUT
from evaluate_topic_continuation_v02302 import metrics

class TopicContinuationTests(unittest.TestCase):
    def test_training_rows(self):
        self.assertEqual(validate(build()),12)
    def test_same_prompts(self):
        rows=build()
        expected=[]
        for topic in TRAIN:
            expected.extend(["人: "+topic+"について話を続けて",
                             "人: "+topic+"の面白いところを教えて"])
        self.assertEqual([r["user"] for r in rows],expected)
    def test_all_answers_changed_from_old(self):
        rows=build()
        original=[answer for pair in TRAIN.values() for answer in pair]
        self.assertTrue(all(r["assistant"]!=a and r["assistant"].startswith(a)
                            for r,a in zip(rows,original)))
    def test_holdout_isolated(self):
        self.assertFalse(set(TRAIN)&set(HOLDOUT))
        prompts="\n".join(r["user"] for r in build())
        self.assertTrue(all(h not in prompts for h in HOLDOUT))
    def test_two_sentence_topic_coverage(self):
        s=metrics("カレー","カレーは香辛料で味が変わる。玉ねぎを炒めると香りが出る。")
        self.assertTrue(s["two_plus_sentences"])
        self.assertTrue(s["lexical_topic_in_second_sentence"])
    def test_generic_is_not_grounded(self):
        s=metrics("宇宙探査","そうですね。何が好きですか。")
        self.assertFalse(s["lexical_topic_coverage"])
        self.assertFalse(s["lexical_topic_in_second_sentence"])
    def test_single_sentence(self):
        self.assertFalse(metrics("写真撮影","写真は面白い。")["two_plus_sentences"])
if __name__=="__main__":unittest.main()
