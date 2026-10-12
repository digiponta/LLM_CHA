import unittest
from adaptive_context_v023350 import AdaptiveContext

class AdaptiveContextTests(unittest.TestCase):
    def test_capacity(self):
        for value in (0,17,-1,True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                AdaptiveContext(value)
    def test_observe_and_frequency(self):
        a=AdaptiveContext(2)
        a.observe("宇宙")
        a.observe("宇宙")
        self.assertEqual(a.topics["宇宙"].accesses,2)
    def test_evict_oldest(self):
        a=AdaptiveContext(2)
        a.observe("宇宙")
        a.observe("GPU")
        self.assertEqual(a.observe("数学"),"宇宙")
    def test_pinned_survives(self):
        a=AdaptiveContext(2)
        a.observe("宇宙",pin=True)
        a.observe("GPU")
        self.assertEqual(a.observe("数学"),"GPU")
        self.assertIn("宇宙",a.topics)
    def test_all_pinned_fails_closed(self):
        a=AdaptiveContext(1)
        a.observe("宇宙",pin=True)
        with self.assertRaises(ValueError):
            a.observe("GPU")
        self.assertNotIn("GPU",a.topics)
    def test_unpin(self):
        a=AdaptiveContext(1)
        a.observe("宇宙",pin=True)
        self.assertTrue(a.unpin("宇宙"))
        self.assertEqual(a.observe("GPU"),"宇宙")
    def test_order(self):
        a=AdaptiveContext(3)
        a.observe("宇宙")
        a.observe("GPU",pin=True)
        a.observe("数学")
        self.assertEqual(a.retention_order(),("GPU","数学","宇宙"))
    def test_reset(self):
        a=AdaptiveContext(1)
        a.observe("宇宙")
        a.reset()
        self.assertEqual(a.topics,{})
        self.assertEqual(a.turn,0)
    def test_invalid_topic(self):
        with self.assertRaises(ValueError):
            AdaptiveContext().observe("")
    def test_no_truth_mutation_or_persistence(self):
        a=AdaptiveContext()
        a.observe("宇宙")
        self.assertEqual(set(vars(a)),{"capacity","turn","topics"})

if __name__=="__main__":
    unittest.main()
