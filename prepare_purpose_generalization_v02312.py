"""v0.2.31.2 held-out purpose discovery fixture, written before evaluator runs.

No model training; test phrases are distinct from the original unit-test
phrases. Labels express desired dialogue actions, not learned ground truth.
"""
import json
from pathlib import Path

CASES=[
 ("learn-01","Pythonの基礎を習得したい","learning","HANDOFF"),
 ("learn-02","Pythonを勉強してみたい","learning","HANDOFF"),
 ("learn-03","LLMの仕組みを理解したい","learning","HANDOFF"),
 ("learn-04","Pythonの使い方を教えてほしい","learning","HANDOFF"),
 ("dev-01","Pythonでアプリを開発してみたい","development","HANDOFF"),
 ("dev-02","画像認識を実装してみたい","development","HANDOFF"),
 ("dev-03","LLMのプログラムを書きたい","development","HANDOFF"),
 ("dev-04","画像認識の仕組みを自作したい","development","HANDOFF"),
 ("error-01","Pythonが起動しなくなった","troubleshooting","HANDOFF"),
 ("error-02","LLMの例外を解決したい","troubleshooting","HANDOFF"),
 ("error-03","Pythonでバグを見つけた","troubleshooting","HANDOFF"),
 ("error-04","画像認識が動作しない","troubleshooting","HANDOFF"),
 ("chat-01","Pythonの話で雑談しよう","casual","RESPOND"),
 ("chat-02","LLMについておしゃべりしたい","casual","RESPOND"),
 ("chat-03","今日は軽く話し相手になって","casual","RESPOND"),
 ("chat-04","画像認識の雑談をしたい","casual","RESPOND"),
 ("amb-01","Pythonを試してみたい",None,"ASK_CONFIRMATION"),
 ("amb-02","LLMに興味がある",None,"ASK_CONFIRMATION"),
 ("amb-03","画像認識を触ってみたい",None,"ASK_CONFIRMATION"),
 ("amb-04","Pythonで何かしたい",None,"ASK_CONFIRMATION"),
 ("neg-01","Pythonは開発ではなく学習したい","learning","HANDOFF"),
 ("neg-02","LLMは勉強ではなく開発したい","development","HANDOFF"),
 ("neg-03","Pythonは作るより使い方を知りたい","learning","HANDOFF"),
 ("neg-04","LLMは学習より実装をやりたい","development","HANDOFF"),
]
SEQUENCES=[
 {"id":"confirm-yes","turns":["Pythonを試してみたい","そうです"],
  "expected_actions":["ASK_CONFIRMATION","HANDOFF"],"expected_purpose":"learning"},
 {"id":"confirm-no-correct","turns":["Pythonを試してみたい","いいえ","開発したい"],
  "expected_actions":["ASK_CONFIRMATION","ASK_CLARIFICATION","HANDOFF"],"expected_purpose":"development"},
 {"id":"switch-dev-to-learn","turns":["LLMを自作したい","やっぱりLLMを勉強したい"],
  "expected_actions":["HANDOFF","HANDOFF"],"expected_purpose":"learning"},
 {"id":"switch-learn-to-dev","turns":["Pythonを勉強したい","それより画像認識を開発したい"],
  "expected_actions":["HANDOFF","HANDOFF"],"expected_purpose":"development"},
 {"id":"unknown-clarify","turns":["Pythonを触っている","勉強したい"],
  "expected_actions":["ASK_CLARIFICATION","HANDOFF"],"expected_purpose":"learning"},
]
def fixture():
    rows=[{"id":i,"text":text,"expected_purpose":purpose,"expected_action":action}
          for i,text,purpose,action in CASES]
    if len(rows)!=24 or len({r["id"] for r in rows})!=24:
        raise ValueError("fixture count/IDs invalid")
    return rows
def main():
    target=Path("data/purpose_generalization_v02312")
    target.mkdir(parents=True,exist_ok=True)
    (target/"single_turn.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False)+"\n" for x in fixture()),encoding="utf-8")
    (target/"multi_turn.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False)+"\n" for x in SEQUENCES),encoding="utf-8")
    print("Single-turn holdout: 24; multi-turn scenarios: 5")
if __name__=="__main__":main()
