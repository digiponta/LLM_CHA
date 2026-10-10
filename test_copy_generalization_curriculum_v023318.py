import unittest
from copy_generalization_curriculum_v023318 import make_stage_sets,variants,as_rows

class CurriculumTests(unittest.TestCase):
    def test_templates(self):
        values=variants("赤い","本","机","置きます")
        self.assertEqual(len(values),4)
        self.assertEqual(values[0],"赤い本を机に置きます。")
        self.assertTrue(all(values))
    def test_stage_disjointness(self):
        stages,(control_val,control_test)=make_stage_sets(42,16,8,8)
        all_train=[];all_val=[];all_test=[]
        for name,group in stages.items():
            self.assertEqual(len(group["train"]),16)
            self.assertEqual(len(group["val"]),8)
            self.assertEqual(len(group["test"]),8)
            all_train+=group["train"];all_val+=group["val"];all_test+=group["test"]
        self.assertEqual(len(set(all_train)),len(all_train))
        self.assertFalse(set(all_train)&set(all_val))
        self.assertFalse(set(all_train)&set(all_test))
        self.assertFalse(set(all_val)&set(all_test))
        self.assertFalse(set(control_val+control_test)&set(all_train+all_val+all_test))
    def test_reproducibility(self):
        self.assertEqual(make_stage_sets(42,10,5,5),make_stage_sets(42,10,5,5))
    def test_bad_counts(self):
        with self.assertRaises(ValueError):make_stage_sets(42,0,5,5)
    def test_copy_rows(self):
        self.assertEqual(as_rows(["赤い本を机に置きます。"])[0]["answer"],"赤い本を机に置きます。")
if __name__=="__main__":unittest.main()
