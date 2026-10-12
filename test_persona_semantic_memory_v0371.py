import tempfile
import unittest
from pathlib import Path
from persona_semantic_memory_v0371 import evidence,persona_reply

class PersonaMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"persona.txt"
        self.path.write_text("量子力学は不思議だ。数学も面白い。\n量子力学は、ある見方では物理の表現。",encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_evidence_provenance(self):
        rows=evidence(self.path,"量子力学")
        self.assertEqual([r.line for r in rows],[1,2])
    def test_no_factual_verification(self):
        self.assertTrue(all(r.factual_truth=="NOT_ASSESSED" for r in evidence(self.path,"量子力学")))
    def test_persona_attributed(self):
        answer,rows=persona_reply(self.path,"量子力学")
        self.assertIn("この人格の原文",answer)
        self.assertEqual(len(rows),2)
    def test_missing_fails_without_generation(self):
        answer,rows=persona_reply(self.path,"宇宙")
        self.assertIn("見つかりません",answer)
        self.assertEqual(rows,[])
    def test_line_stable_ids(self):
        self.assertEqual(evidence(self.path,"数学"),evidence(self.path,"数学"))
    def test_limit(self):
        self.assertEqual(len(evidence(self.path,"量子力学",1)),1)
    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):evidence(self.path," ")
    def test_invalid_limit_rejected(self):
        with self.assertRaises(ValueError):evidence(self.path,"数学",31)
    def test_no_mutation(self):
        before=self.path.read_bytes()
        persona_reply(self.path,"量子力学")
        self.assertEqual(before,self.path.read_bytes())
    def test_chat_command_wired(self):
        source=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn('if command.startswith("/persona "):',source)
        self.assertIn("factual_truth={entry.factual_truth}",source)
if __name__=="__main__":unittest.main()
