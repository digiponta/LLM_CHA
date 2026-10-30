"""Deterministic inference-time rejection cache, keyed to evidence and model revision."""
import hashlib
import json
import re
from pathlib import Path

def normalize_concept_query(question):
    q=re.sub(r"\s+","",str(question or ""))
    for suffix in ("について詳しく説明してください","について説明してください","を詳しく説明してください","を説明してください","について教えてください","を教えてください","とは何ですか","とは"):
        if q.endswith(suffix) and len(q)>len(suffix):
            return q[:-len(suffix)]
    return q

def cache_key(topic,excerpt,model_identity):
    payload=json.dumps([str(topic).strip(),str(excerpt).strip(),str(model_identity).strip()],ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class RejectionReuse:
    def __init__(self,path):
        self.path=Path(path)
    def find(self,topic,excerpt,model_identity):
        key=cache_key(topic,excerpt,model_identity)
        if not self.path.exists():return None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try: record=json.loads(line)
            except json.JSONDecodeError:continue
            if record.get("key")==key and str(record.get("gate","")).startswith("REJECT_"):
                return record
        return None
    def record(self,topic,excerpt,model_identity,candidate,gate):
        if not str(gate).startswith("REJECT_"):raise ValueError("NOT_REJECTED")
        key=cache_key(topic,excerpt,model_identity)
        old=self.find(topic,excerpt,model_identity)
        if old:return "DUPLICATE"
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps({"key":key,"topic":topic,"model_identity":str(model_identity),
                "candidate":candidate,"gate":gate},ensure_ascii=False)+"\n")
        return "RECORDED"

def negative_signal_counts(path):
    path=Path(path)
    counts={"recorded":0,"not_trained":0}
    if not path.exists():return counts
    for line in path.read_text(encoding="utf-8").splitlines():
        try:r=json.loads(line)
        except json.JSONDecodeError:continue
        if r.get("signal")=="NEGATIVE":
            counts["recorded"]+=1
            if r.get("training_status")=="NOT_TRAINED":counts["not_trained"]+=1
    return counts
