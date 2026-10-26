import tempfile
import unittest
from dataclasses import dataclass
from semantic_live_bridge_v0113 import process_turn
from semantic_dialogue_bridge_v0112 import DialogueBridge

@dataclass
class Out:
    text: str
    termination_reason: str = 'MAX_TOKENS'

@dataclass
class Memory:
    hit: bool = True
    answer: str = '記憶側の回答'
    provenance: str = 'corpus:unverified'

class RetryFallbackTest(unittest.TestCase):
    def test_fallback_shows_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = DialogueBridge(directory)
            result = process_turn('人類とは',generate=lambda q:Out('人類は'),retrieve=lambda s:Memory(),bridge=bridge,regenerate=lambda q,i:Out('人類は'))
            self.assertEqual(result['action'],'GENERATION_QUALITY_REVIEW')
            self.assertEqual(result['memory_reference'],'記憶側の回答')
            self.assertEqual(result['memory_approval'],'NOT_ATTESTED')
            self.assertFalse(list(bridge.tickets.root.glob('*.json')))
