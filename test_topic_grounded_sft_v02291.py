import unittest
from prepare_topic_grounded_preformatted_v02291 import convert
from prepare_topic_grounded_v02290 import TRAIN,HOLDOUT

class GroundedSFTTests(unittest.TestCase):
    def test_prompt_alignment(self):
        rows=convert([{"user":"カレーについて話を続けて","assistant":"カレーは香辛料を使うよ。"}])
        self.assertEqual(rows[0]["user"],"人: カレーについて話を続けて")
        self.assertEqual(rows[0]["assistant"],"カレーは香辛料を使うよ。")
        self.assertEqual(rows[0]["user"]+"\nAI: ","人: カレーについて話を続けて\nAI: ")
    def test_reject_double_format(self):
        with self.assertRaises(ValueError):convert([{"user":"人: カレー","assistant":"カレーです"}])
    def test_split_disjoint(self):
        self.assertFalse(set(TRAIN)&set(HOLDOUT))
    def test_training_exposures(self):
        self.assertEqual(len(TRAIN)*2*18,216)
if __name__=="__main__":unittest.main()
