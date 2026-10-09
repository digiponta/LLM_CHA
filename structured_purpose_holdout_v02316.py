"""v0.2.31.6: frozen structured purpose evaluation fixture.

A prospective diagnostic set designed to probe generalization. Do not tune
v0.2.31.5 parser against these rows and then claim a pristine holdout.
"""
CASES=[
 # single positive purpose
 ("learn-a","Pythonを習得したい","Python",["learning"],"UNSPECIFIED","POSITIVE","HANDOFF"),
 ("learn-b","LLMの基本を覚えたい","LLM",["learning"],"UNSPECIFIED","POSITIVE","HANDOFF"),
 ("develop-a","画像認識のツールを製作したい","画像認識",["development"],"UNSPECIFIED","POSITIVE","HANDOFF"),
 ("develop-b","Pythonでアプリを組み上げたい","Python",["development"],"UNSPECIFIED","POSITIVE","HANDOFF"),
 ("trouble-a","Pythonが起動できず困っている","Python",["troubleshooting"],"UNSPECIFIED","POSITIVE","HANDOFF"),
 ("trouble-b","LLMの出力がおかしい","LLM",["troubleshooting"],"UNSPECIFIED","POSITIVE","HANDOFF"),
 ("casual-a","Pythonのことを気軽に話そう","Python",["casual"],"UNSPECIFIED","POSITIVE","RESPOND"),
 ("casual-b","LLMについておしゃべりしませんか","LLM",["casual"],"UNSPECIFIED","POSITIVE","RESPOND"),
 # multiple goals / ordered goals
 ("multi-a","LLMを勉強して、開発もしたい","LLM",["learning","development"],"UNSPECIFIED","POSITIVE","PLAN"),
 ("multi-b","Pythonを学んでから自作したい","Python",["learning","development"],"SEQUENTIAL","POSITIVE","PLAN"),
 ("multi-c","画像認識を実装して、それから学習したい","画像認識",["development","learning"],"SEQUENTIAL","POSITIVE","PLAN"),
 ("multi-d","LLMのエラーを直してから開発したい","LLM",["troubleshooting","development"],"SEQUENTIAL","POSITIVE","PLAN"),
 # preference/negation
 ("neg-a","Pythonは作るより勉強したい","Python",["learning"],"PREFERENCE","NEGATED_ALTERNATIVE","HANDOFF"),
 ("neg-b","LLMの学習じゃなく開発したい","LLM",["development"],"PREFERENCE","NEGATED_ALTERNATIVE","HANDOFF"),
 ("neg-c","画像認識を実装するより仕組みを学びたい","画像認識",["learning"],"PREFERENCE","NEGATED_ALTERNATIVE","HANDOFF"),
 ("neg-d","Pythonは勉強ではなく作りたい","Python",["development"],"PREFERENCE","NEGATED_ALTERNATIVE","HANDOFF"),
 # ambiguous or no goals
 ("amb-a","Pythonが気になっている","Python",[],"UNSPECIFIED","POSITIVE","ASK_CONFIRMATION"),
 ("amb-b","LLMを試すか迷っている","LLM",[],"UNSPECIFIED","POSITIVE","ASK_CONFIRMATION"),
 ("amb-c","画像認識に興味を持った","画像認識",[],"UNSPECIFIED","POSITIVE","ASK_CONFIRMATION"),
 ("unknown-a","今日はどうしよう",None,[],"UNSPECIFIED","POSITIVE","ASK_CLARIFICATION"),
 ("unknown-b","12345678",None,[],"UNSPECIFIED","POSITIVE","ASK_CLARIFICATION"),
 ("unknown-c","少し考えている",None,[],"UNSPECIFIED","POSITIVE","ASK_CLARIFICATION"),
]
def fixture():
    return [{"id":id,"text":text,"topic":topic,"purposes":purposes,
             "relation":relation,"polarity":polarity,"action":action}
            for id,text,topic,purposes,relation,polarity,action in CASES]
