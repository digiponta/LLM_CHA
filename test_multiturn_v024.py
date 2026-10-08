import unittest
from prepare_multiturn_v024 import pairs
class MultiTurnTests(unittest.TestCase):
    def test_history_format(self):
        row={"utterances":[{"interlocutor_id":"A","text":"本を読んでいます"},{"interlocutor_id":"B","text":"何の本？"},{"interlocutor_id":"A","text":"SFです"},{"interlocutor_id":"B","text":"面白そう。"}]}
        result=list(pairs(row,2))
        self.assertEqual(result[-1]["user"],"人: 本を読んでいます\nAI: 何の本？\n人: SFです")
        self.assertEqual(result[-1]["assistant"],"面白そう。")
    def test_persona_metadata_not_used(self):
        row={"persona":"secret","utterances":[{"interlocutor_id":"a","text":"元気？"},{"interlocutor_id":"b","text":"元気"}]}
        self.assertNotIn("secret",str(list(pairs(row))))
    def test_same_speaker_skipped(self):
        row={"utterances":[{"interlocutor_id":"a","text":"はい"},{"interlocutor_id":"a","text":"そう"},{"interlocutor_id":"b","text":"ええ"}]}
        self.assertEqual(list(pairs(row)),[])
if __name__=="__main__":unittest.main()
