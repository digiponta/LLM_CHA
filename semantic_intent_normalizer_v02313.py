"""v0.2.31.3: auditable rule-based semantic intent normalization.

Diagnostic development examples in v0.2.31.2 are now SEEN development
data; reserve v0.2.31.3 fresh fixtures for prospective testing.
This is not an embedding model or LLM_SEM integration.
"""
import json,re
from dataclasses import asdict
from purpose_confidence_v02311 import DSS,respond as legacy_respond

# Priority: explicit preference contrasts first, then narrow paraphrases.
RULES=(
 ("prefer-develop",r"(学習|勉強)より(実装|開発)を?やりたい",r"勉強ではなく開発したい"),
 ("prefer-learn",r"(作る|開発)より(使い方を知りたい|学習したい|勉強したい)",r"開発ではなく勉強したい"),
 ("learn-master",r"習得したい",r"勉強したい"),
 ("learn-understand",r"理解したい",r"勉強したい"),
 ("learn-explore",r"勉強してみたい",r"勉強したい"),
 ("learn-usage",r"使いこなしたい",r"使い方を知りたい"),
 ("develop-try",r"開発してみたい|実装してみたい",r"開発したい"),
 ("develop-code",r"プログラムを書きたい",r"開発したい"),
 ("trouble-start",r"起動しなくなった|立ち上がらない",r"エラーが出た"),
 ("trouble-bug",r"バグを見つけた|バグが出た",r"エラーが出た"),
 ("trouble-run",r"動作しない|動かなくなった",r"エラーが出た"),
 ("ambiguous-try",r"試してみたい",r"試したい"),
)
def normalize(text):
    normalized=text
    applied=[]
    for name,pattern,replacement in RULES:
        result,n=re.subn(pattern,replacement,normalized)
        if n:
            normalized=result
            applied.append(name)
    return normalized,applied

def respond(dss,text):
    normalized,rules=normalize(text)
    state,action,message=legacy_respond(dss,normalized)
    return state,action,message,{"raw":text,"normalized":normalized,"rules":rules}

def main():
    dss=DSS()
    print("LLM_CHA Semantic Intent Normalization v0.2.31.3")
    print("Commands: /state /reset /quit")
    while True:
        try:text=input("You> ")
        except (EOFError,KeyboardInterrupt):break
        if text.strip()=="/quit":break
        if text.strip()=="/state":
            print(json.dumps(asdict(dss),ensure_ascii=False,indent=2));continue
        if text.strip()=="/reset":
            dss=DSS();print("DSS reset");continue
        dss,action,answer,trace=respond(dss,text)
        print(f'CHA[{dss.state}/{action},confidence={dss.confidence:.2f}]> {answer}')
        print("NORM>",json.dumps(trace,ensure_ascii=False))
if __name__=="__main__":main()
