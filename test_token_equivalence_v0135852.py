import unittest
from train_token_equivalence_v0135852 import target_ids
class FakeTokenizer:
 eos_id=3
 def encode(self,text,add_bos=False,add_eos=False):
  # This intentionally normalizes fullwidth question mark, matching observed tokenizer behavior.
  ids=[ord(ch) for ch in text.replace("？","?")]
  return ([1] if add_bos else [])+ids+([3] if add_eos else [])
class Tests(unittest.TestCase):
 def test_teacher_ids_contain_eos_and_normalized_question_mark(self):
  ids=target_ids(FakeTokenizer(),{"assistant":"眠いんだね。休めそう？"})
  self.assertEqual(ids[-2:], [ord("?"),3])
 def test_raw_text_differs_even_when_token_text_canonical(self):
  self.assertNotEqual("眠いんだね。休めそう?","眠いんだね。休めそう？")
 def test_nkf_normalized_text_equal(self):
  import unicodedata
  self.assertEqual(unicodedata.normalize("NFKC","休めそう？"),unicodedata.normalize("NFKC","休めそう?"))
if __name__=="__main__":unittest.main()
