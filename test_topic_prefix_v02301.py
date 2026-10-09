import unittest
from prepare_topic_prefix_v02301 import build
from prepare_topic_grounded_v02290 import build as source_rows
from prepare_topic_grounded_preformatted_v02291 import convert

class PrefixChangeTests(unittest.TestCase):
    def setUp(self):
        self.old=[{"user":r["user"],"assistant":r["assistant"]}
                  for r in source_rows() if r["split"]=="train"]
    def test_all_twelve_changed(self):
        new,changed=build(self.old)
        self.assertEqual(changed,12)
        self.assertEqual(len(new),12)
    def test_prompts_identical(self):
        new,_=build(self.old)
        self.assertEqual([r["user"] for r in convert(self.old)],[r["user"] for r in new])
    def test_content_retained(self):
        new,_=build(self.old)
        self.assertTrue(all(n["assistant"].endswith(o["assistant"]) for n,o in zip(new,self.old)))
    def test_holdout_not_used(self):
        self.assertTrue(all("深海探査" not in r["user"] for r in build(self.old)[0]))
    def test_invalid_count(self):
        with self.assertRaises(ValueError):build(self.old[:11])
if __name__=="__main__":unittest.main()
