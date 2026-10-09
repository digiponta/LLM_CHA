"""LLM_CHA v0.2.31.5 structured purpose prototype.

Purpose evidence (lexical vector) and explicit linguistic structure are
separated. Not a trained semantic parser or an LLM_SEM encoder.
"""
from dataclasses import dataclass,field,asdict
import re,json
from semantic_purpose_estimator_v02314 import SemanticPurposeEstimator
from purpose_confidence_v02311 import topic_of

PURPOSES=("learning","development","troubleshooting","casual")
CUES={
 "learning":r"勉強|学習|習得|覚え|理解|学び|知りた|教えて|仕組み",
 "development":r"開発|実装|作りた|自作|作る|組み立て|製作|制作|コードを書|プログラムを書",
 "troubleshooting":r"エラー|バグ|例外|動かな|動作しな|起動しな|停止|不具合|困って",
 "casual":r"雑談|おしゃべり|話しませんか|話そう|会話を楽し|話し相手",
}
AMBIGUOUS=r"興味|気にな|触ってみ|試してみ|試したい|迷って"
NEGATION=r"ではなく|じゃなく|より|ないで"
ORDER=r"してから|した後|それから|まず.+(?:次に|あとで)|(?:勉強|学習).+から.+(?:開発|作)"
@dataclass
class PurposeStructure:
    topic:str|None=None
    purposes:list[str]=field(default_factory=list)
    relation:str="UNSPECIFIED"
    polarity:str="POSITIVE"
    status:str="NEEDS_CLARIFICATION"
    confidence:float=0.0
    evidence:dict=field(default_factory=dict)

def extract(text,estimator=None,threshold=0.25,margin=0.04):
    estimator=estimator or SemanticPurposeEstimator()
    prediction=estimator.predict(text,threshold=threshold,margin=margin)
    spans=[]
    for purpose,pattern in CUES.items():
        for m in re.finditer(pattern,text):
            spans.append((m.start(),m.end(),purpose,m.group()))
    spans.sort()
    positive=[]
    for _,_,p,_ in spans:
        if p not in positive:positive.append(p)
    polarity="NEGATED_ALTERNATIVE" if re.search(NEGATION,text) else "POSITIVE"
    relation="SEQUENTIAL" if re.search(ORDER,text) else ("ALTERNATIVE" if "それとも" in text else "UNSPECIFIED")
    # Resolve simple comparisons by preferring the goal appearing after
    # the contrastive operator. Keep both in evidence.
    chosen=list(positive)
    contrast=re.search(r"(ではなく|じゃなく|より)",text)
    if contrast and len(positive)>=2:
        after=[p for start,end,p,_ in spans if start>=contrast.end()]
        if after:
            chosen=[p for p in after if p in positive]
            chosen=list(dict.fromkeys(chosen))
            relation="PREFERENCE"
    if re.search(AMBIGUOUS,text) and not chosen:
        status="NEEDS_CONFIRMATION"
    elif chosen:
        status="READY" if (len(chosen)==1 or relation in ("SEQUENTIAL","PREFERENCE")) else "NEEDS_PLANNING"
    elif prediction["accepted"]:
        chosen=[prediction["purpose"]]
        # Similarity-only acceptance is insufficient to skip confirmation.
        status="NEEDS_CONFIRMATION"
    else:
        status="NEEDS_CLARIFICATION"
    return PurposeStructure(
        topic=topic_of(text),
        purposes=chosen,
        relation=relation,
        polarity=polarity,
        status=status,
        confidence=prediction["similarity"],
        evidence={"purpose_cues":[{"purpose":p,"surface":surface,"start":start}
                                  for start,_,p,surface in spans],
                  "vector_candidate":prediction["candidate"],
                  "vector_accepted":prediction["accepted"],
                  "vector_margin":prediction["margin"]})
def action_for(s):
    if s.status=="READY":return "HANDOFF"
    if s.status=="NEEDS_PLANNING":return "PLAN"
    if s.status=="NEEDS_CONFIRMATION":return "ASK_CONFIRMATION"
    return "ASK_CLARIFICATION"
def main():
    model=SemanticPurposeEstimator()
    print("Structured Semantic Purpose v0.2.31.5; /quit to exit")
    while True:
        try:line=input("You> ")
        except (EOFError,KeyboardInterrupt):break
        if line.strip()=="/quit":break
        parsed=extract(line,model)
        print(json.dumps({"action":action_for(parsed),**asdict(parsed)},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
