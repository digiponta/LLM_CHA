"""Prepare v0.13.58 replay inputs, with explicit audited source selection.

This never invents conversation or persona pairs. Each dialogue record must
carry approval=true and user/assistant strings. All outputs are line-oriented
UTF-8 text for train_replay_mixed_v01358.py. Only --run writes files.
"""
import argparse,hashlib,json,re
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def foundation_rows(source):
    rows=[line.strip() for line in source.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not rows:raise ValueError("empty foundation source")
    return list(dict.fromkeys(rows))

def dialogue_rows(source,domain):
    rows=[]
    for n,line in enumerate(source.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():continue
        try:r=json.loads(line)
        except json.JSONDecodeError as e:raise ValueError(f"{source}:{n}: invalid JSONL") from e
        if not isinstance(r,dict):raise ValueError(f"{source}:{n}: object required")
        if r.get("approved") is not True:
            raise ValueError(f"{source}:{n}: approved=true required for every pair")
        user=r.get("user");assistant=r.get("assistant")
        if not isinstance(user,str) or not isinstance(assistant,str) or not user.strip() or not assistant.strip():
            raise ValueError(f"{source}:{n}: user/assistant required")
        if "\n" in user or "\n" in assistant or "\r" in user or "\r" in assistant:
            raise ValueError(f"{source}:{n}: multiline pairs not supported")
        if domain=="persona" and not r.get("persona_reviewed",False):
            raise ValueError(f"{source}:{n}: persona_reviewed=true required")
        rows.append(f"人: {user.strip()} AI: {assistant.strip()}")
    if not rows:raise ValueError("empty dialogue source")
    return list(dict.fromkeys(rows))

def prepare(foundation,conversation,persona,output_dir,run=False):
    inputs=[foundation,conversation,persona]
    outputs=[output_dir/f"replay_{domain}_train.txt" for domain in ("foundation","conversation","persona")]
    audit=output_dir/"replay_data_audit_v013581.json"
    if len({p.resolve() for p in inputs})!=3:raise ValueError("source files must be distinct")
    if any(p.resolve()==q.resolve() for p in [*outputs,audit] for q in inputs):
        raise ValueError("input/output collision")
    for p in inputs:
        if not p.is_file():raise FileNotFoundError(f"missing source: {p}")
        if any(token in p.name.lower() for token in ("holdout","test","eval","validation")):
            raise ValueError(f"evaluation source forbidden: {p}")
    for p in [*outputs,audit]:
        if p.exists():raise FileExistsError(f"output exists; refusing overwrite: {p}")
    data={"foundation":foundation_rows(foundation),
          "conversation":dialogue_rows(conversation,"conversation"),
          "persona":dialogue_rows(persona,"persona")}
    seen={}
    for domain,lines in data.items():
        for line in lines:
            normalized=" ".join(line.split())
            if normalized in seen and seen[normalized]!=domain:
                raise ValueError(f"exact cross-domain overlap: {seen[normalized]} / {domain}")
            seen[normalized]=domain
    result={"version":"v0.13.58.1","status":"PREPARED" if run else "PREFLIGHT_OK",
        "counts":{k:len(v) for k,v in data.items()},
        "source_sha256":{str(p):sha(p) for p in inputs},
        "outputs":{k:str(p) for k,p in zip(data,outputs)},
        "human_approval_policy":"conversation approved=true; persona approved=true and persona_reviewed=true",
        "independent_holdout_verified":False,
        "training_approved":False}
    if run:
        output_dir.mkdir(parents=True,exist_ok=True)
        for (domain,lines),out in zip(data.items(),outputs):
            with out.open("x",encoding="utf-8",newline="\n") as f:f.write("\n".join(lines)+"\n")
        with audit.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--foundation-source",type=Path,required=True,help="training-only UTF-8 lines")
    ap.add_argument("--conversation-jsonl",type=Path,required=True,help="reviewed {user,assistant,approved:true} pairs")
    ap.add_argument("--persona-jsonl",type=Path,required=True,help="reviewed {user,assistant,approved:true,persona_reviewed:true} pairs")
    ap.add_argument("--output-dir",type=Path,default=Path("data"))
    ap.add_argument("--run",action="store_true")
    a=ap.parse_args()
    result=prepare(a.foundation_source,a.conversation_jsonl,a.persona_jsonl,a.output_dir,a.run)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
