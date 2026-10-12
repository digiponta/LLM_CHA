import unittest
from pathlib import Path
from context_recovery_gpu_accept_v023344 import TOPIC, run
from longterm_context_v02340 import ContextCheckpoint

class GpuAcceptanceHarnessTests(unittest.TestCase):
    def test_topic(self):
        self.assertEqual(TOPIC,"宇宙")

    def test_checkpoint_roundtrip(self):
        c=ContextCheckpoint()
        c.remember(TOPIC,"0123456789abcdef01234567")
        self.assertEqual(ContextCheckpoint.restore(c.export()).topics,c.topics)

    def test_missing_corpus_fails(self):
        with self.assertRaises(FileNotFoundError):
            run(Path("missing_gpu_accept_corpus_unsupported.jsonl"))

if __name__=="__main__":
    unittest.main()
