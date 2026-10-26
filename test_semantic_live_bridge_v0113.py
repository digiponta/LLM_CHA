import tempfile
import unittest
from dataclasses import dataclass
from semantic_live_bridge_v0113 import process_turn,extract_subject
from semantic_dialogue_bridge_v0112 import DialogueBridge

@dataclass
class Retrieved:
    hit:bool
    answer:str
    provenance:str="corpus:unverified"
class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.bridge=DialogueBridge(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_subject(self):
        self.assertEqual(extract_subject("物質波とは"),"物質波")
    def test_different_candidates_trigger_unknown_not_conflict(self):
        got=[]
        result=process_turn("物質波とは",generate=lambda q:"物質波は電磁波",
                            retrieve=lambda s:(got.append(s) or Retrieved(True,"物質波はドブロイ波")),
                            bridge=self.bridge)
        self.assertEqual(got,["物質波"])
        self.assertEqual(result["action"],"ASK_USER")
        self.assertEqual(result["divergence_status"],"UNKNOWN")
        self.assertEqual(result["memory_approval"],"NOT_ATTESTED")
    def test_persistence_and_preference(self):
        kwargs=dict(generate=lambda q:"モデル回答",retrieve=lambda s:Retrieved(True,"メモリ回答"),
                    bridge=self.bridge)
        first=process_turn("質問とは",**kwargs)
        self.bridge.review(first["ticket_id"],"prefer_b")
        second=process_turn("質問とは",**kwargs)
        self.assertEqual(second["action"],"USER_PREFERENCE")
        self.assertEqual(second["answer"],"メモリ回答")
        self.assertEqual(second["factual_truth"],"UNVERIFIED")
    def test_memory_miss_no_ticket(self):
        r=process_turn("未知とは",generate=lambda q:"生成結果",
                       retrieve=lambda s:Retrieved(False,""),bridge=self.bridge)
        self.assertEqual(r["action"],"MEMORY_MISS")
        self.assertEqual(list(self.bridge.tickets.root.glob("*.json")),[])
    def test_same_surface_no_ticket(self):
        r=process_turn("質問",generate=lambda q:"解読/分析",
                       retrieve=lambda s:Retrieved(True,"解読／分析"),bridge=self.bridge)
        self.assertEqual(r["action"],"CANONICALIZED_LEXICAL")
    def test_empty_generation(self):
        r=process_turn("質問",generate=lambda q:"",retrieve=lambda s:Retrieved(True,"記憶"),
                       bridge=self.bridge)
        self.assertEqual(r["action"],"GENERATION_UNAVAILABLE")
    def test_different_question_no_preference(self):
        kw=dict(generate=lambda q:"生成",retrieve=lambda s:Retrieved(True,"記憶"),bridge=self.bridge)
        first=process_turn("Aとは",**kw)
        self.bridge.review(first["ticket_id"],"prefer_a")
        self.assertEqual(process_turn("Bとは",**kw)["action"],"ASK_USER")
if __name__=="__main__":unittest.main()
