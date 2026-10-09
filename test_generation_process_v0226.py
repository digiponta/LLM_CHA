import unittest
from diagnose_generation_process_v0226 import ACKS
from prepare_context_generalization_v0225 import TRAIN,HOLDOUT,make

class GenerationProcessTests(unittest.TestCase):
    def test_short_ack_baseline(self):
        self.assertIn("そう。",ACKS)
        self.assertEqual(len(set(ACKS)),len(ACKS))
    def test_same_user_question_and_separate_topics(self):
        rows=[make(t) for t in TRAIN+HOLDOUT]
        self.assertEqual({r["user"].split("人: ")[-1] for r in rows},{"その話を続けて"})
        self.assertFalse({t[1] for t in TRAIN}&{t[1] for t in HOLDOUT})
    def test_reference_is_not_generic_ack(self):
        for item in TRAIN+HOLDOUT:
            self.assertNotIn(item[2],ACKS)
if __name__=="__main__":unittest.main()
