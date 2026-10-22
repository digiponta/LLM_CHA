"""v0.7.2: isolated Candidate-only GPU sandbox training.

No approval, promotion, /sleep, or trusted state changes. The trainer receives
only pending candidate pairs. Results are experimental and not deployable.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def select_candidates(memory):
    rows=memory.candidates()
    selected=[r for r in rows if r["status"]=="PENDING"]
    # Existing contradictory proposals are ambiguous; require review first.
    questions={}
    for row in selected:
        key=row["question"].strip()
        if key in questions and questions[key]!=row["answer"]:
            raise ValueError("conflicting pending candidate answers: "+key)
        questions[key]=row["answer"]
    return selected

def commands_for_training(trainer,base,tokenizer,pairs,state,output,epochs,lr):
    return [sys.executable,str(Path(trainer).resolve()),
        "--chat-data",str(pairs),"--base-model",str(base),
        "--tokenizer",str(tokenizer),"--output",str(output),"--state",str(state),
        "--replay-data",str(pairs.parent/"no_replay.txt"),
        "--stability-data",str(pairs.parent/"no_stability.jsonl"),
        "--epochs",str(epochs),"--learning-rate",str(lr),
        "--batch-size","1","--manual-weight","1",
        "--trusted-replay-weight","0","--stability-weight","0",
        "--replay-ratio","0","--recovery-stabilization-epochs","0",
        "--tiny-threshold","100000"]

def run(approved_path,candidate_path,base_path,tokenizer_path,output_dir,
        trainer="online_train.py",epochs=3,lr=3e-6):
    memory=DualMemory(approved_path,candidate_path)
    selected=select_candidates(memory)
    if not selected:
        raise ValueError("No pending candidate rows; nothing to sandbox-train.")
    output_dir=Path(output_dir).resolve()
    base=Path(base_path).resolve()
    tokenizer=Path(tokenizer_path).resolve()
    approved=Path(approved_path).resolve()
    candidates=Path(candidate_path).resolve()
    trainer=Path(trainer).resolve()
    for path in (base,tokenizer,trainer):
        if not path.is_file():raise FileNotFoundError(path)
    output_dir.mkdir(parents=True,exist_ok=True)
    model=output_dir/"candidate-sandbox-v072.pt"
    state=output_dir/"candidate-sandbox-state-v072.json"
    report=output_dir/"candidate-sandbox-report-v072.json"
    protected={base,tokenizer,approved,candidates}
    if any(p in protected for p in (model,state,report)):
        raise ValueError("Sandbox output overlaps protected files")
    # Use a fresh state: must not accidentally inherit trusted learning state.
    if model.exists() or state.exists() or report.exists():
        raise FileExistsError("Sandbox output already exists; use a new output directory")
    baseline_hash=digest(base)
    approved_hash=digest(approved) if approved.exists() else None
    candidate_hash=digest(candidates) if candidates.exists() else None
    with tempfile.TemporaryDirectory(prefix="llm-cha-v072-") as temporary:
        temp=Path(temporary)
        pairs=temp/"sandbox.jsonl"
        with pairs.open("w",encoding="utf-8") as f:
            for row in selected:
                # Existing online_train accepts trusted source labels only.
                # This classification exists in a transient sandbox file,
                # not in the Approved Semantic Memory.
                f.write(json.dumps({"user":row["question"],
                    "assistant":row["answer"],"source":"chat-manual"},ensure_ascii=False)+"\n")
        cmd=commands_for_training(trainer,base,tokenizer,pairs,state,model,epochs,lr)
        proc=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace")
    unchanged=(digest(base)==baseline_hash and
        (digest(approved) if approved.exists() else None)==approved_hash and
        (digest(candidates) if candidates.exists() else None)==candidate_hash)
    result={"version":"v0.7.2","kind":"EXPERIMENTAL_SANDBOX",
            "pending_count":len(selected),"pending_ids":[r["id"] for r in selected],
            "source_ids":[r["source_id"] for r in selected],
            "training_returncode":proc.returncode,
            "protected_sources_unchanged":unchanged,
            "checkpoint_exists":model.is_file(),
            "checkpoint":str(model),"state":str(state),
            "stdout_tail":proc.stdout[-3000:],"stderr_tail":proc.stderr[-2000:],
            "trusted_deployable":False,"auto_promote":False,
            "pass":proc.returncode==0 and unchanged and model.is_file()}
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if not unchanged:raise RuntimeError("Protected input changed unexpectedly")
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--approved",default="data/approved_v071.jsonl")
    ap.add_argument("--candidates",default="data/candidates_v071.jsonl")
    ap.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    ap.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--output-dir",default="results/candidate_sandbox_v072")
    ap.add_argument("--epochs",type=int,default=3)
    ap.add_argument("--learning-rate",type=float,default=3e-6)
    a=ap.parse_args()
    result=run(a.approved,a.candidates,a.base,a.tokenizer,a.output_dir,
               epochs=a.epochs,lr=a.learning_rate)
    print(json.dumps({"pass":result["pass"],"pending_count":result["pending_count"],
            "protected_sources_unchanged":result["protected_sources_unchanged"],
            "checkpoint":result["checkpoint"]},ensure_ascii=False))
    raise SystemExit(0 if result["pass"] else 1)
if __name__=="__main__":main()
