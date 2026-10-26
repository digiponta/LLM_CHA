import unittest
from topic_keyed_context_v09756 import TopicContext

class TopicKeyedTests(unittest.TestCase):
    def test_first_question(self):
        c=TopicContext()
        self.assertIn("スファレライト",c.observe("スファレライトの成分は"))
    def test_followup(self):
        c=TopicContext();c.observe("スファレライトの成分は")
        self.assertIn("スファレライト",c.observe("化学組成を知りたい"))
    def test_intervening_preference(self):
        c=TopicContext();c.observe("スファレライトの成分は")
        self.assertIsNone(c.observe("宝石としてのスファレライトが好きです"))
        self.assertIsNone(c.observe("きれいです"))
        self.assertIn("スファレライト",c.observe("化学組成を知りたい"))
    def test_explicit_restart(self):
        c=TopicContext();c.observe("スファレライトの成分は")
        self.assertIn("スファレライト",c.observe("スファレライトの成分"))
    def test_multiple_topics(self):
        c=TopicContext()
        c.observe("スファレライトの成分は")
        c.observe("方解石の成分は")
        self.assertEqual(len(c.topics),2)
        self.assertIn("方解石",c.observe("化学組成を知りたい"))
    def test_definition_not_captured(self):
        c=TopicContext()
        self.assertIsNone(c.observe("スファレライトとは"))
    def test_command_not_captured(self):
        self.assertIsNone(TopicContext().observe("/exit"))
    def test_does_not_invent_formula(self):
        c=TopicContext();reply=c.observe("スファレライトの成分")
        self.assertNotIn("ZnS",reply)
        self.assertEqual(c.topics["スファレライト"]["status"],"SOURCE_NEEDED")

if __name__=="__main__":unittest.main()
