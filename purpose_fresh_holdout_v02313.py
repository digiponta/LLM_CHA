"""Prospective v0.2.31.3 fixtures; not used to construct RULES."""
FRESH=[
 ("fresh-learn-1","Pythonの文法をもっと覚えたい","learning","HANDOFF"),
 ("fresh-learn-2","LLMを詳しく勉強したい","learning","HANDOFF"),
 ("fresh-dev-1","Pythonで道具を作りたい","development","HANDOFF"),
 ("fresh-dev-2","画像認識のツールを組み立てたい","development","HANDOFF"),
 ("fresh-error-1","Pythonで例外が発生する","troubleshooting","HANDOFF"),
 ("fresh-error-2","LLMが正常に動作しない","troubleshooting","HANDOFF"),
 ("fresh-chat-1","LLMのことでおしゃべりしよう","casual","RESPOND"),
 ("fresh-chat-2","Pythonの話をしませんか","casual","RESPOND"),
 ("fresh-amb-1","Pythonをちょっと触ってみたい",None,"ASK_CONFIRMATION"),
 ("fresh-amb-2","LLMが気になっている",None,"ASK_CONFIRMATION"),
 ("fresh-neg-1","開発じゃなくPythonの勉強をしたい","learning","HANDOFF"),
 ("fresh-neg-2","LLMは学ぶより作る方がいい","development","HANDOFF"),
]
FRESH_SEQUENCES=[
 {"id":"fresh-confirm","turns":["Pythonをちょっと触ってみたい","うん"],
  "actions":["ASK_CONFIRMATION","HANDOFF"],"purpose":"learning"},
 {"id":"fresh-correct","turns":["LLMを自作したい","やっぱりPythonの基礎を習得したい"],
  "actions":["HANDOFF","HANDOFF"],"purpose":"learning"},
]
def fixture():
    return [{"id":i,"text":t,"expected_purpose":p,"expected_action":a} for i,t,p,a in FRESH]
