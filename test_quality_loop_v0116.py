import unittest
from generation_quality_gate_v0114 import assess_generation

class QualityLoopTests(unittest.TestCase):
    def test_loop(self):
        text='人類は、人類は、人類にとって、人類は人類は人類の行動する。'
        self.assertIn('JAPANESE_PHRASE_LOOP', assess_generation(text).reasons)
    def test_normal(self):
        self.assertEqual(assess_generation('人類は宇宙を観測する。人類は技術を用いる。').status, 'VALID')

if __name__=='__main__': unittest.main()
