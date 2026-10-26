import tempfile
import unittest
from dataclasses import dataclass
from generation_quality_gate_v0114 import assess_generation
from semantic_live_bridge_v0113 import process_turn
from semantic_dialogue_bridge_v0112 import DialogueBridge

@dataclass
class Generated:
    text:str
    termination_reason:str
@dataclass
class Memory:
    hit:bool=True
    answer:str="人類は活動を続けている"
    provenance:str="unverified"
class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.bridge=DialogueBridge(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_cap(self):
        self.assertIn("MAX_TOKENS",assess_generation(Generated("人類は、","MAX_TOKENS")).reasons)
    def test_replacement_char(self):
        self.assertIn("REPLACEMENT_CHARACTER",assess_generation("大�").reasons)
    def test_normal(self):
        self.assertEqual(assess_generation(Generated("磁石は力を及ぼす。","EOS")).status,"VALID")
    def test_empty(self):
        self.assertEqual(assess_generation("").status,"INVALID")
    def test_incomplete_prevents_ticket(self):
        result=process_turn("人類とは",generate=lambda q:Generated("人類は、","MAX_TOKENS"),
                            retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(result["action"],"GENERATION_QUALITY_REVIEW")
        self.assertFalse(list(self.bridge.tickets.root.glob("*.json")))
    def test_invalid_unicode_prevents_ticket(self):
        result=process_turn("創世記とは",generate=lambda q:Generated("洪水の�","EOS"),
                            retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(result["action"],"GENERATION_QUALITY_REVIEW")
    def test_valid_still_asks_user(self):
        result=process_turn("宇宙とは",generate=lambda q:Generated("宇宙は広がる。","EOS"),
                            retrieve=lambda s:Memory(),bridge=self.bridge)
        self.assertEqual(result["action"],"ASK_USER")
    def test_same_surface_still_canonicalizes(self):
        result=process_turn("質問とは",generate=lambda q:Generated("解読／分析","EOS"),
                            retrieve=lambda s:Memory(answer="解読/分析"),bridge=self.bridge)
        self.assertEqual(result["action"],"CANONICALIZED_LEXICAL")
if __name__=="__main__":unittest.main()
