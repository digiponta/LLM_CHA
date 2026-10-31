import unittest
from argparse import Namespace
from train_real_persona_pilot_v013588296 import command
class TestPilotCommand(unittest.TestCase):
 def test_training_isolation_and_weight(self):
  a=Namespace(dataset="pilot.jsonl",base="base.pt",tokenizer="tok.json",output_model="new.pt",state="new_state.json",epochs=2,learning_rate=1e-5)
  c=command(a)
  self.assertEqual(c[c.index("--manual-weight")+1],"1")
  self.assertEqual(c[c.index("--output")+1],"new.pt")
  self.assertEqual(c[c.index("--base-model")+1],"base.pt")
if __name__=="__main__":unittest.main()
