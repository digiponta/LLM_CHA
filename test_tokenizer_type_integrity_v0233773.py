import unittest
from tokenizer_bpe import BPETokenizer

class _Backend:
    def encode(self, text, add_special_tokens=False):
        class Result: ids=[12,13]
        return Result()

class _RejectBackend:
    def encode(self,text,add_special_tokens=False):
        raise TypeError("TextInputSequence must be str")

class TokenizerTypeIntegrityTests(unittest.TestCase):
    def tokenizer(self,backend):
        t=BPETokenizer()
        t.backend=backend
        t.fitted=True
        return t
    def test_reject_none_before_backend(self):
        with self.assertRaisesRegex(TypeError,"expected str; received NoneType"):
            self.tokenizer(_Backend()).encode(None)
    def test_reject_list_before_backend(self):
        with self.assertRaisesRegex(TypeError,"expected str; received list"):
            self.tokenizer(_Backend()).encode(["こんにちは"])
    def test_str_goes_to_backend(self):
        self.assertEqual(self.tokenizer(_Backend()).encode("こんにちは"),[12,13])
    def test_backend_rejection_identified(self):
        with self.assertRaisesRegex(TypeError,"backend rejected a str input"):
            self.tokenizer(_RejectBackend()).encode("こんにちは")
    def test_invalid_input_does_not_silently_stringify(self):
        with self.assertRaises(TypeError):
            self.tokenizer(_Backend()).encode(("こんにちは",))
if __name__=="__main__":unittest.main()
