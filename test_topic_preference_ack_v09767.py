import unittest
from topic_preference_ack_v09767 import acknowledge

class Tests(unittest.TestCase):
    def test_reported(self):
        self.assertEqual(acknowledge("私は、スファレライトが好きです","スファレライト"),
                         "スファレライトが好きなんだね。どんなところが気に入っている？")
    def test_no_pronoun(self):
        self.assertIsNotNone(acknowledge("スファレライトが大好きです"))
    def test_not_science_question(self):
        self.assertIsNone(acknowledge("スファレライトの屈折率は？"))
    def test_not_why(self):
        self.assertIsNone(acknowledge("なぜカットが難しいの？"))
    def test_reject_negative(self):
        self.assertIsNone(acknowledge("スファレライトが好きではない"))
    def test_no_learning(self):
        self.assertIsNone(acknowledge("/sleep"))

if __name__=="__main__":
    unittest.main()
