"""Evidence-bound multi-sense definitions; conservative opt-in registry.

Only sentences present in the source are accepted. No LLM inference or training.
"""
import re
from question_aware_evidence_v013588255 import split_sentences
from evidence_conditioned_generation_v013588228 import evidence_gate

# Each sense needs a distinct meaning cue; bare mention of the term is insufficient.
SENSES={
 "メモリ":(
  {"sense":"COMPUTER_MEMORY","question_cues":("コンピュータ","計算機","RAM","主記憶","メモリ"),
   "evidence_cues":("主記憶","RAM","データを記憶","記憶装置"),
   "anchor":("メモリ","主記憶"),"label":"コンピュータのメモリ"},
  {"sense":"HUMAN_MEMORY","question_cues":("人間の記憶","記憶力","思い出"),
   "evidence_cues":("人間の記憶","経験を覚え","脳に保存","記憶する能力"),
   "anchor":("記憶","メモリ"),"label":"人間の記憶"}),
 "モデル":(
  {"sense":"MACHINE_LEARNING_MODEL","question_cues":("機械学習","AI","LLM","学習モデル"),
   "evidence_cues":("機械学習","学習済み","予測を行う","ニューラルネットワーク"),
   "anchor":("モデル",),"label":"機械学習モデル"},
  {"sense":"PHYSICAL_MODEL","question_cues":("物理モデル","物理学","物理現象"),
   "evidence_cues":("物理現象","物理法則","物理モデル","数理的に表す"),
   "anchor":("モデル",),"label":"物理モデル"})
}
def _question_sense(question,senses):
    matched=[sense for sense in senses if any(cue in question for cue in sense["question_cues"] if cue not in ("メモリ","モデル"))]
    if len(matched)==1:return matched[0]
    return None

def resolve(question,evidence):
    q=str(question or "").strip()
    topic=next((t for t in SENSES if t in q),None)
    if topic is None:return None
    if evidence.get("status")!="EVIDENCE":return None
    senses=SENSES[topic]
    preferred=_question_sense(q,senses)
    candidates=[]
    for s in split_sentences(evidence.get("excerpt","")):
        if not 15<=len(s)<=300:continue
        if evidence_gate(s,evidence)[0]!="ACCEPT_SOURCE_EXTRACT":continue
        for sense in senses:
            if any(a in s for a in sense["anchor"]) and any(c in s for c in sense["evidence_cues"]):
                if re.search(r"(?:とは|は、|を指す|である|という|意味する)",s):
                    candidates.append((sense,s))
    options=[(sense,s) for sense,s in candidates if preferred is None or sense["sense"]==preferred["sense"]]
    if preferred is not None and not options:
        return {"status":"ABSTAIN_SENSE_NOT_GROUNDED","answer":
                "指定された語義に対応する定義は、この資料から確認できません。"}
    unique={item[0]["sense"] for item in options}
    if preferred is None and len(unique)!=1:
        return {"status":"ABSTAIN_AMBIGUOUS_SENSE","answer":
                "複数の語義があります。コンピュータ／人間の記憶、機械学習／物理学などの対象を指定してください。"}
    if not options:return None
    sense,s=options[0]
    caution=("同じ語には別の分野の意味もあります。今回は「"+sense["label"]+"」として説明しています。")
    return {"status":"BOUND_SENSE_NOTICE","subject":topic,"sense":sense["sense"],
            "relation":"definition","value":s,"sentence":s,
            "answer":"「"+sense["label"]+"」について、資料には次の説明があります。\n"+s+
                     "\n※語義の注意: "+caution+"\n出典: "+str(evidence.get("url",""))+"（外部未検証）"}
