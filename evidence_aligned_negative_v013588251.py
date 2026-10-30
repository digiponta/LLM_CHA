"""Snapshot exact GUI evidence-candidate prompt together with rejected output."""
import hashlib
import json
from pathlib import Path
from evidence_aware_route_v013588236 import encode_request,decode_request,generation_prompt

def capture_negative(path,evidence,candidate,gate,model_revision=None):
    if not str(gate).startswith("REJECT_"):raise ValueError("NOT_REJECTED")
    if evidence.get("status")!="EVIDENCE":raise ValueError("NO_EVIDENCE")
    topic,excerpt=decode_request(encode_request(evidence["topic"],evidence["excerpt"]))
    candidate=" ".join(str(candidate).split())
    if not candidate:raise ValueError("EMPTY_CANDIDATE")
    prompt=generation_prompt(topic,excerpt)
    identity=hashlib.sha256(json.dumps([prompt,candidate,gate],ensure_ascii=False).encode()).hexdigest()
    row={"id":identity,"topic":topic,"prompt":prompt,"rejected_answer":candidate,
         "gate":gate,"signal":"NEGATIVE","training_status":"NOT_TRAINED",
         "source_url":str(evidence.get("url","")),"model_revision":model_revision,
         "prompt_version":"evidence_aware_route_v013588236"}
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:old=json.loads(line)
            except json.JSONDecodeError:continue
            if old.get("id")==identity:return "DUPLICATE"
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,ensure_ascii=False)+"\n")
    return "RECORDED"

def load_aligned(path):
    if not Path(path).exists():return []
    rows={}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:r=json.loads(line)
        except json.JSONDecodeError:continue
        if (r.get("signal")=="NEGATIVE" and r.get("training_status")=="NOT_TRAINED"
            and r.get("prompt_version")=="evidence_aware_route_v013588236"
            and str(r.get("prompt","")).startswith("人: ")
            and str(r.get("rejected_answer","")).strip()):
            rows[r["id"]]=r
    return list(rows.values())
