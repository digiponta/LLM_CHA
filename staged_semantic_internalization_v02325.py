"""LLM_CHA v0.2.32.5 staged DSS -> Semantic Memory -> LLM lifecycle.

No model is trained or promoted here. Promotion is explicitly gated by
external free-generation, generalization and retention evidence.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,datetime
from evidence_dialogue_state_v02319 import DialogueState
from contextual_purpose_composition_v02321 import step,generation_context

STATES=("MEMORIZED","TRAINING","VALIDATING","INTERNALIZED","FAILED")
def digest(context):
    identity={k:context.get(k) for k in ("user_input","topic","purposes","relation","action")}
    return hashlib.sha256(json.dumps(identity,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:20]

def teacher_record(state,utterance,action,reply,approved=False,approved_answer=None):
    context=generation_context(state,action,utterance)
    if action.startswith("ASK"):
        return None
    if approved_answer is not None and not approved:
        raise ValueError("Reviewed answer requires explicit approval")
    return {"id":digest(context),"context":context,"dss_response":reply,
            "approved_answer":approved_answer if approved else None,
            "teacher_status":"APPROVED" if approved else "PENDING_REVIEW",
            "teacher_provenance":"reviewed" if approved else "dss_controller",
            "lifecycle":"MEMORIZED","checkpoint":None,
            "evidence":{}}

def read_memory(path):
    p=Path(path)
    if not p.exists():return {}
    rows={}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():continue
        r=json.loads(line)
        if r["id"] in rows:raise ValueError(f"Duplicate memory id: {r['id']}")
        rows[r["id"]]=r
    return rows

def write_memory(path,rows):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text("".join(json.dumps(rows[k],ensure_ascii=False)+"\n" for k in sorted(rows)),encoding="utf-8")
    tmp.replace(p)

def memorize(path,record):
    rows=read_memory(path)
    if record is None:return None
    prior=rows.get(record["id"])
    # Never erase review state, evidence or promotion on a repeated input.
    if prior:return prior
    rows[record["id"]]=record;write_memory(path,rows)
    return record

def approve(path,record_id,answer):
    if not answer.strip():raise ValueError("Teacher answer must not be empty")
    rows=read_memory(path);r=rows[record_id]
    if r["lifecycle"]!="MEMORIZED":
        raise ValueError("Only untrained memorized records can be reviewed")
    r["approved_answer"]=answer.strip()
    r["teacher_status"]="APPROVED";r["teacher_provenance"]="human_review"
    write_memory(path,rows)
    return r

def training_queue(path):
    return [r for r in read_memory(path).values()
            if r["lifecycle"]=="MEMORIZED" and r["teacher_status"]=="APPROVED"]

def transition(path,record_id,target,checkpoint=None,evidence=None):
    rows=read_memory(path);r=rows[record_id];old=r["lifecycle"]
    permitted={"MEMORIZED":{"TRAINING"},"TRAINING":{"VALIDATING","FAILED"},
               "VALIDATING":{"INTERNALIZED","FAILED"},
               "INTERNALIZED":{"FAILED"},"FAILED":{"MEMORIZED"}}
    if target not in permitted[old]:raise ValueError(f"Illegal transition: {old} -> {target}")
    if target=="TRAINING" and r["teacher_status"]!="APPROVED":
        raise ValueError("Review teacher answer before training")
    if target=="VALIDATING" and not checkpoint:
        raise ValueError("Candidate checkpoint required")
    if target=="INTERNALIZED":
        checks=("free_generation","unseen_generalization","retention","purpose_fidelity")
        proof=evidence or {}
        if not r["checkpoint"] or not all(proof.get(x) is True for x in checks):
            raise ValueError("Independent promotion evidence + candidate checkpoint required")
    if target=="VALIDATING":r["checkpoint"]=checkpoint
    if target=="INTERNALIZED":r["evidence"]=dict(evidence)
    if target=="FAILED":r["evidence"]={"reason":(evidence or {}).get("reason","validation_or_runtime_failure")}
    r["lifecycle"]=target
    write_memory(path,rows);return r

def route(path,record_id):
    record=read_memory(path).get(record_id)
    if not record:return "DSS_FALLBACK"
    if (record["lifecycle"]=="INTERNALIZED" and record["checkpoint"] and
        all(record["evidence"].get(k) is True for k in
            ("free_generation","unseen_generalization","retention","purpose_fidelity"))):
        return "LLM_DIRECT_ELIGIBLE"
    return "DSS_FALLBACK"

def handle(d,utterance,memory_path):
    d,action,reply=step(d,utterance)
    record=memorize(memory_path,teacher_record(d,utterance,action,reply))
    selected=route(memory_path,record["id"]) if record else "DSS_FALLBACK"
    # Routing selection is advisory; no model inference is executed in this stage.
    return d,{"action":action,"controller_reply":reply,"record_id":record["id"] if record else None,
              "teacher_status":record["teacher_status"] if record else None,
              "lifecycle":record["lifecycle"] if record else None,"route":selected}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--memory",default="data/dss_semantic_memory_v02325.jsonl")
    a=p.parse_args()
    d=DialogueState()
    print("LLM_CHA v0.2.32.5 Staged Internalization Prototype")
    print("Commands: /state /queue /reset /quit")
    while True:
        try:text=input("You> ").strip()
        except (EOFError,KeyboardInterrupt):break
        if text=="/quit":break
        if text=="/reset":d=DialogueState();print("DSS reset");continue
        if text=="/state":print(json.dumps(asdict(d),ensure_ascii=False,indent=2));continue
        if text=="/queue":
            print(json.dumps([{"id":r["id"],"topic":r["context"]["topic"]} for r in training_queue(a.memory)],ensure_ascii=False,indent=2));continue
        if not text:continue
        d,result=handle(d,text,a.memory)
        print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
