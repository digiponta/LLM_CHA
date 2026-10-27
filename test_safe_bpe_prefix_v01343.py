import unittest
from safe_bpe_prefix_v01343 import safe_prefix_ids

class Dummy:
    def encode(self,s):return list(s.encode("utf-8"))
    def decode(self,ids):return bytes(ids).decode("utf-8",errors="replace")
class SafePrefixTests(unittest.TestCase):
    def test_mid_character_moves_back(self):
        tok=Dummy();r=safe_prefix_ids(tok,"猫と犬。",1)
        self.assertEqual(r["actual_tokens"],0)
        self.assertNotIn("�",r["prefix"]+r["reference_continuation"])
    def test_valid_boundary(self):
        tok=Dummy();r=safe_prefix_ids(tok,"猫と犬。",3)
        self.assertEqual(r["actual_tokens"],3)
        self.assertEqual(r["prefix"],"猫")
    def test_reconstruct(self):
        tok=Dummy()
        for n in range(10):
            r=safe_prefix_ids(tok,"吾輩は猫。",n)
            self.assertEqual(r["prefix"]+r["reference_continuation"],"吾輩は猫。")
    def test_out_of_range(self):
        self.assertIsNone(safe_prefix_ids(Dummy(),"猫",100))
if __name__=="__main__":unittest.main()
