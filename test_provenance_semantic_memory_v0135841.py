import copy,unittest
from provenance_semantic_memory_v0135841 import answer,resolve,PROBES,ALLOWED,SUBJECT
def row(relation,value="夏目漱石",id="x"):
 return {"record_id":id,"subject":SUBJECT,"relation":relation,"value":value,
 "source_id":"lit-author","approval_state":ALLOWED,"active":True,"production_approved":False}
class Tests(unittest.TestCase):
 def test_answer_and_provenance(self):
  r=answer("『吾輩は猫である』の作者は誰？",[row("author")])
  self.assertEqual(r["status"],"ANSWERED")
  self.assertEqual(r["facts"][0]["source_id"],"lit-author")
 def test_experimental_gate(self):
  self.assertEqual(answer("『吾輩は猫である』の作者は誰？",[row("author")],False)["status"],"ABSTAIN")
 def test_conflicts_abstain(self):
  self.assertEqual(answer("『吾輩は猫である』の作者は誰？",[row("author"),row("author","別名","y")])["reason"],"CONFLICTING_FACTS")
 def test_unreviewed_abstain(self):
  r=row("author");r["approval_state"]="PENDING"
  self.assertEqual(answer("『吾輩は猫である』の作者は誰？",[r])["status"],"ABSTAIN")
 def test_false_yesno_abstain(self):
  self.assertEqual(answer("『吾輩は猫である』を書いたのは福沢諭吉ですか？",[row("author")])["status"],"ABSTAIN")
 def test_unrelated_abstain(self):
  self.assertEqual(answer("量子力学とは",[row("author")])["status"],"ABSTAIN")
if __name__=="__main__":unittest.main()
