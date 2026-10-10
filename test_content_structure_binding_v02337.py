import unittest
from unittest.mock import patch
import content_structure_binding_v02337 as m
class BindingTests(unittest.TestCase):
    def test_disjoint(self):self.assertTrue(m.validate())
    def test_pairing(self):
        rows=m.construct(m.TRAIN_ITEMS)
        self.assertEqual(len(rows),10)
        for item in m.TRAIN_ITEMS["definition"]:
            pair=[r for r in rows if r["topic"]==item]
            self.assertEqual(len(pair),2)
            self.assertEqual(pair[0]["answer"],pair[1]["answer"])
            self.assertNotEqual(pair[0]["prompt"],pair[1]["prompt"])
    def test_grounded_plan(self):
        row=m.construct({"definition":[],"procedure":["機器点検"]})[1]
        self.assertIn("開始=",row["prompt"])
        self.assertIn("まず",row["answer"])
        self.assertIn("次に",row["answer"])
        self.assertIn("最後に",row["answer"])
    def test_topic_overlap_rejected(self):
        with patch.object(m,"TEST_ITEMS",{"definition":["CPU"],"procedure":["機器点検"]}):
            with self.assertRaisesRegex(ValueError,"Topic leakage"):m.validate()
    def test_no_embedded_semantics_when_ungrounded(self):
        rows=m.construct(m.TEST_ITEMS)
        self.assertTrue(all(("内容:" in r["prompt"])==r["grounded"] for r in rows))
if __name__=="__main__":unittest.main()
