import unittest
from tokenizer_bpe import BPETokenizer

class Encoded:
    def __init__(self, ids): self.ids=ids
class ScalarFails:
    def encode(self,*a,**k):raise TypeError("TextInputSequence must be str")
    def encode_batch(self, texts,**k):
        assert texts==["こんにちは"]
        return [Encoded([3,4,5])]
class BothFail(ScalarFails):
    def encode_batch(self,*a,**k):raise TypeError("batch unavailable")
class OtherFailure(ScalarFails):
    def encode(self,*a,**k):raise TypeError("unrelated bug")
class ScalarWorks(ScalarFails):
    def encode(self,*a,**k):return Encoded([7])

class TokenizerBackendFallbackTests(unittest.TestCase):
    def tok(self,backend):
        t=BPETokenizer();t.backend=backend;t.fitted=True
        return t
    def test_scalar_str_rejected_then_batch_succeeds(self):
        self.assertEqual(self.tok(ScalarFails()).encode("こんにちは"),[3,4,5])
    def test_scalar_success_unchanged(self):
        self.assertEqual(self.tok(ScalarWorks()).encode("こんにちは"),[7])
    def test_both_fail_explicit(self):
        with self.assertRaisesRegex(RuntimeError,"scalar encode and one-item batch fallback failed"):
            self.tok(BothFail()).encode("こんにちは")
    def test_unrelated_error_not_masked(self):
        with self.assertRaisesRegex(TypeError,"unrelated bug"):
            self.tok(OtherFailure()).encode("こんにちは")
    def test_non_str_rejected(self):
        with self.assertRaisesRegex(TypeError,"received list"):
            self.tok(ScalarFails()).encode(["こんにちは"])
if __name__=="__main__":unittest.main()
