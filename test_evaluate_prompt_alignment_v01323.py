import unittest
from evaluate_prompt_alignment_v01323 import probes

class PromptAlignmentTests(unittest.TestCase):
    def test_three_distinct_prompts(self):
        row={"subject":"時間","user":"原文では時間について何と述べていますか","source_text":"時間を含む記録。"}
        p=probes(row)
        self.assertEqual(len(p),3)
        self.assertEqual(p[0][1],row["user"])
        self.assertIn("時間",p[1][1])
        self.assertIn(row["source_text"],p[2][1])
    def test_no_fabricated_definition(self):
        row={"subject":"始まり","user":"原文では始まりについて","source_text":"始まりと終わりの記録。"}
        self.assertNotIn("始まりとは",probes(row)[0][1])

if __name__=="__main__":unittest.main()
