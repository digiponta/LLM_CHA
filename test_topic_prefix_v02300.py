import unittest
from prepare_topic_prefix_v02300 import make_rows
from prepare_topic_grounded_v02290 import TRAIN,HOLDOUT

class PrefixTests(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(make_rows()),12)
    def test_explicit_topic_first(self):
        for row in make_rows():
            prompt=row["user"][len("人: "):]
            topic=next(t for t in TRAIN if prompt.startswith(t))
            self.assertTrue(row["assistant"].startswith(topic))
    def test_disjoint(self):
        self.assertFalse(set(TRAIN)&set(HOLDOUT))
    def test_holdout_exclusion(self):
        text="\n".join(r["user"] for r in make_rows())
        for topic in HOLDOUT:self.assertNotIn(topic,text)
if __name__=="__main__":unittest.main()
