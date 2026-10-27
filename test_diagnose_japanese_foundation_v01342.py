import tempfile
import unittest
from pathlib import Path
from diagnose_japanese_foundation_v01342 import load_sentences,case_prefixes,char3_overlap,trigram_repeat,summarise

class FakeTokenizer:
    def encode(self,text):return list(range(len(text)))
    def decode(self,ids):return "".join(chr(65+(i%26)) for i in ids)

class FoundationDiagnosticTests(unittest.TestCase):
    def test_gold_prefixes(self):
        rows=case_prefixes(FakeTokenizer(),"あ"*31)
        self.assertEqual([r[0] for r in rows],[0,4,12,24])
        self.assertTrue(all(len(r[1])+len(r[2])==31 for r in rows))
    def test_short_case(self):
        rows=case_prefixes(FakeTokenizer(),"abc")
        self.assertEqual([r[0] for r in rows],[0])
    def test_repetition(self):
        self.assertGreater(trigram_repeat("abababab"),0)
        self.assertEqual(trigram_repeat("あいうえお"),0)
    def test_similarity(self):
        self.assertEqual(char3_overlap("abcdef","abcdef"),1)
        self.assertEqual(char3_overlap("abcdef","uvwxyz"),0)
    def test_dedup_and_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"data.txt"
            good="これは日本語の文章生成を調査するための長さを持った例文です。"
            p.write_text(good+"\n"+good+"\n"+"短い。\n",encoding="utf-8")
            self.assertEqual(load_sentences(p),[good])
    def test_summary(self):
        data=[{"prefix_tokens":0,"mode":"greedy","reference_char3_jaccard":0.2,"repetition":0.0,
               "stop":"eos","continuation":"abc","new_tokens":3}]
        self.assertEqual(summarise(data)["0:greedy"]["eos_rate"],1)

if __name__=="__main__":unittest.main()
