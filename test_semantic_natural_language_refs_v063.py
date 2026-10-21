import unittest
from copy import deepcopy
from conversation_semantic_memory_v042857 import new_memory
from incremental_semantic_memory_v042859 import append, validate
from semantic_natural_language_refs_v063 import (
    attach_natural_language_refs, resolve_natural_language,
)


class NaturalLanguageReferenceTests(unittest.TestCase):
    def sample(self):
        memory = new_memory("conversation-1")
        append(memory, "user", "私は車を持っていない")
        return memory

    def test_reference_resolves_to_original_text(self):
        memory = self.sample()
        ref = memory["propositions"][0]["natural_language_refs"][0]
        self.assertEqual(ref["relation"], "source")
        self.assertEqual(
            resolve_natural_language(memory, ref["uri"]),
            "私は車を持っていない"
        )
        self.assertEqual(memory["propositions"][0]["truth_state"],
                         "USER_REPORTED_UNVERIFIED")
        self.assertFalse(memory["train_ready"])

    def test_idempotent(self):
        memory = self.sample()
        before = deepcopy(memory)
        attach_natural_language_refs(memory)
        self.assertEqual(memory, before)

    def test_legacy_migration(self):
        memory = self.sample()
        memory.pop("natural_language_texts")
        memory.pop("natural_language_refs_version")
        for prop in memory["propositions"]:
            prop.pop("natural_language_refs")
        upgraded = validate(memory)
        self.assertEqual(len(upgraded["natural_language_texts"]), 1)

    def test_multiple_turns_persist(self):
        memory = self.sample()
        append(memory, "user", "私は映画が好き", recent_limit=1)
        self.assertEqual(len(memory["recent_turns"]), 1)
        self.assertEqual(len(memory["natural_language_texts"]), 2)
        for prop in memory["propositions"]:
            uri = prop["natural_language_refs"][0]["uri"]
            self.assertEqual(resolve_natural_language(memory, uri),
                             prop["source_text"])

    def test_integrity_detects_tampering(self):
        memory = self.sample()
        uri = memory["propositions"][0]["natural_language_refs"][0]["uri"]
        memory["natural_language_texts"][uri]["text"] = "偽のテキスト"
        with self.assertRaises(ValueError):
            resolve_natural_language(memory, uri)
        with self.assertRaises(ValueError):
            validate(memory)

    def test_no_fact_no_text_store_entries(self):
        memory = new_memory("conversation-2")
        append(memory, "assistant", "私は車を持っていない")
        self.assertEqual(memory["natural_language_texts"], {})
        self.assertEqual(memory["propositions"], [])


if __name__ == "__main__":
    unittest.main()
