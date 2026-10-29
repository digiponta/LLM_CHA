import unittest
from train_protected_replay_v0135854 import replay_weights
class Tests(unittest.TestCase):
 def test_no_replay(self):
  self.assertEqual(replay_weights(0),(1,0))
 def test_quarter(self):
  self.assertEqual(replay_weights(0.25),(0.75,0.25))
 def test_half(self):
  self.assertEqual(replay_weights(0.5),(0.5,0.5))
 def test_invalid(self):
  with self.assertRaises(ValueError):replay_weights(0.75)
if __name__=="__main__":unittest.main()
