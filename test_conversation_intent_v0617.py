import unittest
from identity_context_v0617 import IdentityContext
from aozora_dialogue_v0610 import AozoraDialogue

class V0617Tests(unittest.TestCase):
    def test_identity_followup(self):
        c=IdentityContext()
        self.assertEqual(c.respond("貴方は")[1],"IDENTITY_CLARIFY")
        self.assertEqual(c.respond("名前は"),("長門有希。","IDENTITY_FOLLOWUP"))
    def test_direct_identity(self):
        self.assertEqual(IdentityContext().respond("貴方の名前は"),("長門有希。","IDENTITY_DIRECT"))
    def test_context_not_leaked(self):
        c=IdentityContext()
        c.respond("貴方は")
        self.assertIsNone(c.respond("宇宙"))
        self.assertIsNone(c.respond("名前は"))
    def test_literary_direct_question(self):
        sample={"789":[{"text":"吾輩は猫である。名前はまだ無い。","provenance":{"work_id":"789","title":"吾輩は猫である","author":"夏目漱石","card_url":"https://www.aozora.gr.jp/cards/000148/card789.html"},"natural_language_refs":[{"uri":"nl://sample"}]}]}
        result=AozoraDialogue(sample).respond("吾輩は猫であるの猫の名前は")
        self.assertEqual(result[1]["route"],"AOZORA_DIRECT_QUESTION")
if __name__=="__main__":unittest.main()
