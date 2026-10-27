import unittest
from train_japanese_foundation_v01344 import verify_corpus,make_examples

AUDIT={"version":"v0.13.43","split":"SOURCE_GROUPED",
       "assignments":{"a":"train","b":"val"},
       "counts":{"train":2,"val":1},
       "source_audit":[{"id":"a"},{"id":"b"}]}
class FakeTokenizer:
    pad_id=0
    def encode(self,text,add_bos=False,add_eos=False):
        return ([1] if add_bos else [])+[ord(ch)%100+3 for ch in text]+([2] if add_eos else [])

class FoundationTrainingTests(unittest.TestCase):
    def test_small_demo_rejected_by_default(self):
        with self.assertRaises(ValueError):
            verify_corpus(["文章A","文章B"],["文章C"],AUDIT)
    def test_demo_allowed(self):
        result=verify_corpus(["文章A","文章B"],["文章C"],AUDIT,allow_demo=True)
        self.assertTrue(result["small_demo"])
    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            verify_corpus(["文章A","文章B"],["文章A"],AUDIT,allow_demo=True)
    def test_count_mismatch(self):
        with self.assertRaises(ValueError):
            verify_corpus(["文章A"],["文章C"],AUDIT,allow_demo=True)
    def test_token_target_shift_and_mask(self):
        dataset=make_examples(["日本語"],FakeTokenizer(),8)
        x,y,mask=dataset[0]
        count=int(mask.sum().item())
        self.assertEqual(x[1:count].tolist(),y[:count-1].tolist())
        self.assertEqual(y[count-1].item(),2)
    def test_truncated_sentence_is_chunked(self):
        dataset=make_examples(["あいうえおかきくけこ"],FakeTokenizer(),4)
        self.assertGreaterEqual(len(dataset),3)
if __name__=="__main__":unittest.main()
