"""Fast static regressions for v0.3.7.3; runtime GPU acceptance remains separate."""
import unittest
from pathlib import Path

class AutoPersonaRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=Path("chat.py").read_text(encoding="utf-8")
    def test_slash_command_removed(self):
        self.assertNotIn('if command.startswith("/persona "):',self.code)
    def test_persona_answer_prompt(self):
        self.assertIn('print(f"persona> {persona_answer}")',self.code)
    def test_only_raw_corpus_fallback(self):
        self.assertIn('dispatch.state == "RAW_CORPUS_ONLY"',self.code)
    def test_truth_block_respected(self):
        self.assertIn('truth_result.runtime_status == "BLOCK"',self.code)
    def test_factual_retrieval_precedes_persona(self):
        self.assertLess(self.code.index('if (\n            dispatch.action == "RETRIEVE"'),self.code.index('print(f"persona> {persona_answer}")'))
    def test_no_persona_when_no_evidence(self):
        self.assertIn('if persona_entries:',self.code)
    def test_response_retained(self):
        self.assertIn('history.append((resolver_query, persona_answer))',self.code)
    def test_no_persona_checkpoint_training(self):
        from persona_semantic_memory_v0371 import persona_reply
        self.assertTrue(callable(persona_reply))

if __name__=="__main__":unittest.main()
