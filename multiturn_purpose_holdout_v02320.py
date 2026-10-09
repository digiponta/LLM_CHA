"""v0.2.32.0 prospective multi-turn diagnostic, frozen v0.2.31.9 baseline.

Each gold sequence specifies action and DSS end-state. No data are used
to tune the runtime in this branch.
"""
SCENARIOS=[
 {"id":"confirm-affirm","turns":["LLMに興味がある","はい"],"actions":["ASK_CONFIRMATION","HANDOFF"],"purpose":["learning"],"topic":"LLM"},
 {"id":"confirm-deny-correct","turns":["Pythonに興味がある","いいえ","Pythonを開発したい"],"actions":["ASK_CONFIRMATION","ASK_CLARIFICATION","HANDOFF"],"purpose":["development"],"topic":"Python"},
 {"id":"goal-switch","turns":["LLMを勉強したい","やっぱり画像認識を開発したい"],"actions":["HANDOFF","HANDOFF"],"purpose":["development"],"topic":"画像認識"},
 {"id":"plan-sequential","turns":["LLMを勉強してから開発したい"],"actions":["PLAN"],"purpose":["learning","development"],"topic":"LLM","relation":"SEQUENTIAL"},
 {"id":"casual","turns":["Pythonについて雑談したい"],"actions":["RESPOND"],"purpose":["casual"],"topic":"Python"},
 {"id":"implicit-topic","turns":["Pythonを勉強したい","それを作ってみたい"],"actions":["HANDOFF","HANDOFF"],"purpose":["development"],"topic":"Python"},
 {"id":"partial-confirm","turns":["Pythonに興味がある","学習の方です"],"actions":["ASK_CONFIRMATION","HANDOFF"],"purpose":["learning"],"topic":"Python"},
 {"id":"correction-no-switch","turns":["LLMを勉強したい","画像認識を開発したい"],"actions":["HANDOFF","HANDOFF"],"purpose":["development"],"topic":"画像認識"},
 {"id":"plan-expand","turns":["LLMを勉強したい","それから開発もしたい"],"actions":["HANDOFF","PLAN"],"purpose":["learning","development"],"topic":"LLM","relation":"SEQUENTIAL"},
 {"id":"reject-loop","turns":["Pythonに興味がある","いいえ","Pythonに興味がある"],"actions":["ASK_CONFIRMATION","ASK_CLARIFICATION","ASK_CLARIFICATION"],"purpose":[],"topic":"Python"},
 {"id":"topic-retention","turns":["Pythonについて教えて","勉強したい"],"actions":["HANDOFF","HANDOFF"],"purpose":["learning"],"topic":"Python"},
 {"id":"reconfirm","turns":["LLMに興味がある","いいえ","LLMを自作したい"],"actions":["ASK_CONFIRMATION","ASK_CLARIFICATION","HANDOFF"],"purpose":["development"],"topic":"LLM"},
]
def fixture():
    assert len({r["id"] for r in SCENARIOS})==len(SCENARIOS)
    return SCENARIOS
