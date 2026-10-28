"""v0.13.58.3: audit and convert reviewed replay pairs into v0.13.58 input.

Foundation defaults to SOURCE-GROUPED training file ONLY. No val/test data
included. Preserve domain labels, reject overlap, and cap repeated exposure.
--run writes outputs; default prints preflight only.
"""
import argparse,hashlib,json
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_pairs(p,persona=False):
    rows=[]
    for i,line in enumerate(p.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():continue
        obj=json.loads(line)
        if obj.get("approved") is not True:raise ValueError(f"{p}:{i}: unapproved")
        if persona and obj.get("persona_reviewed") is not True:
            raise ValueError(f"{p}:{i}: persona not reviewed")
        u=obj.get("user");a=obj.get("assistant")
        if not isinstance(u,str) or not isinstance(a,str) or not u.strip() or not a.strip():
            raise ValueError(f"{p}:{i}: invalid pair")
        if any(ch in u+a for ch in "\r\n"):raise ValueError("multiline pair")
        rows.append((u.strip(),a.strip()))
    if not rows:raise ValueError(f"empty: {p}")
    if len(rows)!=len(set(rows)):raise ValueError(f"duplicate pairs: {p}")
    return rows

def build(foundation,conversation,persona,knowledge,validation,tokenizer=None,
          max_repeat=2,steps=100,allow_small=True):
    if max_repeat<1 or steps<10 or steps%10:raise ValueError("bad repeat/steps")
    foundation_rows=[s.strip() for s in foundation.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if not foundation_rows:raise ValueError("empty foundation")
    if len(foundation_rows)!=len(set(foundation_rows)):raise ValueError("duplicate foundation")
    conv=read_pairs(conversation)
    pers=read_pairs(persona,True)
    know=read_pairs(knowledge)
    val=[]
    for i,s in enumerate(validation.read_text(encoding="utf-8-sig").splitlines(),1):
        if not s.strip():continue
        r=json.loads(s)
        if not isinstance(r,dict) or not isinstance(r.get("user"),str):raise ValueError(f"invalid val row {i}")
        val.append(r["user"].strip())
    reserved=set(val)
    for name,rows in (("conversation",conv),("persona",pers),("knowledge",know)):
        bad=[u for u,a in rows if u in reserved]
        if bad:raise ValueError(f"validation leakage in {name}: {bad[:2]}")
    pairs=conv+pers+know
    if len(pairs)!=len(set(pairs)):raise ValueError("cross-domain duplicate dialogue pair")
    # Knowledge can be grouped with conversation for the three-stream
    # trainer, but source mix is explicitly reported.
    domains={"foundation":foundation_rows,
             "conversation":[f"人: {u} AI: {a}" for u,a in conv+know],
             "persona":[f"人: {u} AI: {a}" for u,a in pers]}
    # Only 3 sources are available plus literature, so the target slots
    # are 30/20/10 for foundation/conversation/persona. Knowledge shares
    # the conversation slot, not an invented fifth percentage.
    required={"foundation":steps*30//100,"conversation":steps*20//100,
              "persona":steps*10//100}
    over={k:{"requested_samples":required[k],"available_unique_lines":len(domains[k]),
             "exposure_multiple":round(required[k]/len(domains[k]),3),
             "within_repeat_cap":required[k]<=len(domains[k])*max_repeat}
          for k in domains}
    allowed=all(row["within_repeat_cap"] for row in over.values())
    counts={k:len(v) for k,v in domains.items()}
    report={"version":"v0.13.58.3","source_counts":{"foundation":len(foundation_rows),
              "conversation":len(conv),"knowledge":len(know),"persona":len(pers)},
            "merged_training_counts":counts,"sampling":over,
            "sample_steps":steps,"max_repeat":max_repeat,
            "sampling_safe":allowed,"training_approved":False,
            "reserved_question_overlap":0,
            "warnings":["Foundation is a small demo, not a validated large foundation dataset.",
                        "Exact validation exclusion does not prove semantic independence.",
                        "Mixed training can still forget; quality gate and human checks remain mandatory."]}
    if tokenizer:
        from tokenizer_bpe import Tokenizer
        tok=Tokenizer.load(str(tokenizer))
        report["bpe_tokens"]={k:sum(len(tok.encode(s,add_bos=True,add_eos=True)) for s in rows)
                              for k,rows in domains.items()}
        report["bpe_tokenizer_sha256"]=digest(tokenizer)
    return domains,report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--foundation",type=Path,default=Path("results/japanese_foundation_corpus_v01343/train.txt"))
    p.add_argument("--conversation",type=Path,default=Path("data/replay_conversation_approved_v013582.jsonl"))
    p.add_argument("--persona",type=Path,default=Path("data/replay_persona_approved_v013582.jsonl"))
    p.add_argument("--knowledge",type=Path,default=Path("data/replay_knowledge_approved_v013582.jsonl"))
    p.add_argument("--validation",type=Path,default=Path("data/nagato_chat_val.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--steps",type=int,default=100)
    p.add_argument("--max-repeat",type=int,default=2)
    p.add_argument("--output-dir",type=Path,default=Path("data"))
    p.add_argument("--report",type=Path,default=Path("results/replay_integration_audit_v013583.json"))
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    inputs=[a.foundation,a.conversation,a.persona,a.knowledge,a.validation,a.tokenizer]
    if any(not f.is_file() for f in inputs):p.error("missing input: "+", ".join(str(f) for f in inputs if not f.is_file()))
    outputs=[a.output_dir/f"replay_{k}_train.txt" for k in ("foundation","conversation","persona")]
    if any(f.resolve() in {q.resolve() for q in inputs} for f in outputs+[a.report]):
        p.error("input/output path collision")
    if a.report.exists() or any(f.exists() for f in outputs):p.error("output exists; refusing overwrite")
    domains,report=build(a.foundation,a.conversation,a.persona,a.knowledge,a.validation,a.tokenizer,
                         a.max_repeat,a.steps)
    report["input_sha256"]={str(f):digest(f) for f in inputs}
    report["status"]="READY_FOR_CONTROLLED_EXPERIMENT" if report["sampling_safe"] else "REPEAT_CAP_EXCEEDED"
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not a.run:return
    if not report["sampling_safe"]:
        p.error("repeat cap exceeded; reduce --steps or change reviewed data, no outputs written")
    a.output_dir.mkdir(parents=True,exist_ok=True);a.report.parent.mkdir(parents=True,exist_ok=True)
    for key,path in zip(("foundation","conversation","persona"),outputs):
        with path.open("x",encoding="utf-8",newline="\n") as f:
            f.write("\n".join(domains[key])+"\n")
    with a.report.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print("written:",*[str(f) for f in outputs],str(a.report))
if __name__=="__main__":main()
