import unittest
from grounded_unapproved_generation_v01321 import grounded_prompt, validate_generation, choose_answer

E={"source_text":"物体の運動は、その物体の時間において、一意な運動している。"}

class GroundedGenerationTests(unittest.TestCase):
    def test_prompt_contains_original_source(self):
        self.assertIn(E["source_text"],grounded_prompt("時間とは",E))
    def test_verbatim_excerpt_passes(self):
        ok,reason=validate_generation("その物体の時間において",E)
        self.assertTrue(ok)
        self.assertEqual(reason,"VERBATIM_SOURCE_EXCERPT")
    def test_fabricated_definition_falls_back(self):
        chosen=choose_answer("時間は宇宙の絶対的尺度である。",E)
        self.assertEqual(chosen["route"],"SOURCE_QUOTATION_FALLBACK")
        self.assertIn(E["source_text"],chosen["answer"])
    def test_empty_falls_back(self):
        self.assertFalse(validate_generation("",E)[0])
    def test_no_automatic_approval(self):
        chosen=choose_answer("その物体の時間において",E)
        self.assertEqual(chosen["route"],"GROUNDED_EXCERPT")
        self.assertIn("未承認",chosen["answer"])

if __name__=="__main__":unittest.main()
