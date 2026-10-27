import unittest
from sweep_rpc_decoding_v01337 import repetition, generic, choose_probes, summarize

class TestDecodingSweep(unittest.TestCase):
    def test_repetition(self):
        self.assertEqual(repetition("abc"), 0)
        self.assertGreater(repetition("abcabcabc"), 0)
    def test_generic(self):
        self.assertTrue(generic("そうですね。"))
        self.assertFalse(generic("そうですね、料理は好きです。"))
    def test_probe_selection_deterministic(self):
        rows = [{"dialogue_id": i//3, "utterance_id": i} for i in range(30)]
        self.assertEqual(choose_probes(rows, 5), choose_probes(rows, 5))
        self.assertEqual(len({r["dialogue_id"] for r in choose_probes(rows, 5)}), 5)
    def test_summary(self):
        x = {"exact_match": False, "repetition": .2, "generated_tokens": 5,
             "generic_reply": True, "text": "そうですね", "hit_max_tokens": False}
        self.assertEqual(summarize([x])["generic_reply"], 1)

if __name__ == "__main__":
    unittest.main()
