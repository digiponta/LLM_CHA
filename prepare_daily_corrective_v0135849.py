"""v0.13.58.49 correction loop: promote reviewed failures to train; rotate holdout.

Never train on unreviewed candidates. Previous holdout prompts are RETIRED from
evaluation after being converted into training samples.
"""
import argparse,json,hashlib
from pathlib import Path

def load(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8-sig").splitlines() if s.strip()]

def build(base,candidates,replacements,output,allow_reviewed=False):
    old=load(base); repairs=load(candidates); fresh=load(replacements)
    if not allow_reviewed:raise ValueError("explicit --accept-reviewed required")
    if output.exists():raise FileExistsError(output)
    if not repairs:raise ValueError("no corrections")
    ids={r["source_id"] for r in repairs}
    prior_holdout={r["id"]:r for r in old if r["split"]=="holdout"}
    if not ids.issubset(prior_holdout):raise ValueError("correction missing from holdout")
    for r in repairs:
        if r.get("review_state")!="ASSISTANT_PROPOSED_REVIEW_REQUIRED":raise ValueError("unexpected review state")
        if r.get("approved_for_training") is not False:raise ValueError("unexpected candidate state")
        if r["user"]!=prior_holdout[r["source_id"]]["user"]:raise ValueError("prompt mismatch")
        if r["assistant"]!=prior_holdout[r["source_id"]]["assistant"]:raise ValueError("reference mismatch")
        if not r["assistant"].strip() or "\ufffd" in r["assistant"]:raise ValueError("invalid answer")
    if any(r["split"]!="holdout" for r in fresh) or len(fresh)<6:raise ValueError("fresh holdout required")
    train=[r for r in old if r["split"]=="train"]
    protected=[r for r in old if r["split"]=="protected"]
    promoted=[{"id":r["id"],"split":"train","category":"corrective_replay",
               "user":r["user"],"assistant":r["assistant"],
               "source":"assistant_proposed_explicitly_accepted_experiment",
               "production_approved":False,"previous_bad_output_ref":r["source_id"]}
              for r in repairs]
    allrows=train+promoted+protected+fresh
    qs=[r["user"].strip() for r in allrows]
    if len(qs)!=len(set(qs)):raise ValueError("train/holdout overlap or duplicates")
    keys=[r["id"] for r in allrows]
    if len(keys)!=len(set(keys)):raise ValueError("duplicate IDs")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text("\n".join(json.dumps(r,ensure_ascii=False) for r in allrows)+"\n",encoding="utf-8")
    return {"status":"REVIEWED_CORRECTIONS_PROMOTED_TO_EXPERIMENTAL_TRAIN",
            "train":len(train)+len(promoted),"promoted":len(promoted),
            "holdout":len(fresh),"protected":len(protected),
            "retired_holdout_ids":sorted(ids),"production_approved":False,
            "independent_holdout":False,"output":str(output),
            "sha256":hashlib.sha256(output.read_bytes()).hexdigest()}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,default=Path("data/daily_sft_expanded_v0135848.jsonl"))
    p.add_argument("--candidates",type=Path,default=Path("data/daily_corrective_candidates_v0135849.jsonl"))
    p.add_argument("--replacements",type=Path,default=Path("data/daily_holdout_rotation_v0135849.jsonl"))
    p.add_argument("--output",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--accept-reviewed",action="store_true")
    a=p.parse_args()
    print(json.dumps(build(a.base,a.candidates,a.replacements,a.output,a.accept_reviewed),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
