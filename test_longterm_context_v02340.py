import unittest
from longterm_context_v02340 import ContextCheckpoint

class LongTermContextTests(unittest.TestCase):
    def test_roundtrip(self):
        c=ContextCheckpoint()
        c.remember("宇宙","abc")
        c.remember("GPU","xyz")
        c.switch("宇宙")
        r=ContextCheckpoint.restore(c.export())
        self.assertEqual(r.export(),c.export())

    def test_no_repeat(self):
        c=ContextCheckpoint()
        c.remember("宇宙","a")
        c.remember("宇宙","a")
        self.assertEqual(c.topics["宇宙"],["a"])

    def test_switch_missing(self):
        self.assertFalse(ContextCheckpoint().switch("不存在"))

    def test_reset(self):
        c=ContextCheckpoint()
        c.remember("宇宙","a")
        c.reset()
        self.assertEqual(c.topics,{})
        self.assertIsNone(c.active_topic)

    def test_schema_guard(self):
        with self.assertRaises(ValueError):
            ContextCheckpoint.restore('{"schema":"other","topics":{}}')

    def test_invalid_topic_rejected(self):
        with self.assertRaises(ValueError):
            ContextCheckpoint().remember("","a")

    def test_invalid_active_topic(self):
        with self.assertRaises(ValueError):
            ContextCheckpoint.restore('{"schema":"llm-cha-context-v02340","topics":{},"active_topic":"missing"}')

    def test_stable_digest(self):
        c=ContextCheckpoint()
        c.remember("宇宙","a")
        self.assertEqual(c.digest(),ContextCheckpoint.restore(c.export()).digest())

if __name__=="__main__":unittest.main()
