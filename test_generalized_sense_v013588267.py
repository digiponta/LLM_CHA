import unittest
from evidence_generalized_sense_v013588267 import resolve

def evidence(text):
    return {"status":"EVIDENCE","topic":"モデル","excerpt":text,"url":"https://example.invalid"}

class SenseTests(unittest.TestCase):
    def test_machine_learning(self):
        e=evidence("機械学習モデルとは、機械学習によって予測を行うモデルである。")
        self.assertEqual(resolve("機械学習モデルとは",e)["sense"],"MACHINE_LEARNING_MODEL")
    def test_physics_missing(self):
        e=evidence("機械学習モデルとは、機械学習によって予測を行うモデルである。")
        self.assertEqual(resolve("物理モデルとは",e)["status"],"ABSTAIN_SENSE_NOT_GROUNDED")
    def test_ambiguous_with_caution(self):
        e=evidence("機械学習モデルとは、機械学習によって予測を行うモデルである。物理モデルとは、物理現象を数理的に表すモデルである。")
        self.assertEqual(resolve("モデルとは",e)["status"],"BOUND_SENSE_NOTICE")

if __name__=="__main__":
    unittest.main()
