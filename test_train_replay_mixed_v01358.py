import tempfile
import unittest
from pathlib import Path
from train_replay_mixed_v01358 import prepare, DOMAINS

class ReplayMixedTests(unittest.TestCase):
    def build(self, root, count=120):
        result = {}
        for domain in DOMAINS:
            p = root / (domain + ".txt")
            p.write_text("\n".join(f"{domain} の文章 {i}" for i in range(count)) + "\n", encoding="utf-8")
            result[domain] = p
        return result

    def test_ratios(self):
        with tempfile.TemporaryDirectory() as d:
            sampled, audit = prepare(self.build(Path(d)))
            self.assertEqual(audit["domain_sampled"], {
                "literature": 160, "foundation": 120,
                "conversation": 80, "persona": 40})
            self.assertEqual(len(sampled), 400)

    def test_reproducible(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self.build(Path(d))
            self.assertEqual(prepare(paths)[0], prepare(paths)[0])

    def test_demo_block(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self.build(Path(d), count=3)
            with self.assertRaises(ValueError):
                prepare(paths)
            _, audit = prepare(paths, allow_small=True)
            self.assertTrue(audit["replay_with_replacement"])

    def test_holdout_block(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self.build(Path(d))
            paths["persona"] = Path(d) / "persona_holdout.txt"
            paths["persona"].write_text("secret", encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare(paths)

    def test_cross_domain_overlap_block(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self.build(Path(d))
            paths["persona"].write_text(paths["foundation"].read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare(paths)

    def test_bad_steps(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                prepare(self.build(Path(d)), steps_per_epoch=101)

if __name__ == "__main__":
    unittest.main()
