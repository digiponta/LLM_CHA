"""Read-only audit of historic online learning fingerprints.

Old state/checkpoint membership is not proof of optimizer exposure.
Never mutate state, logs, or checkpoints.
"""
import argparse
import json
from pathlib import Path
from online_train import (load_chat_jsonl, deduplicate_trusted_rows,
                          pair_fingerprint, load_training_state,
                          checkpoint_trained_fingerprints)

def audit(log_path, state_path, checkpoint_path):
    rows=deduplicate_trusted_rows(load_chat_jsonl(Path(log_path)))
    state=load_training_state(Path(state_path))
    checkpoint=checkpoint_trained_fingerprints(Path(checkpoint_path))
    records=[]
    observed=set()
    for u,a,source in rows:
        fp=pair_fingerprint(u,a)
        observed.add(fp)
        in_state=fp in state
        in_checkpoint=fp in checkpoint
        if in_state and in_checkpoint:
            status="RECORDED_BOTH_UNVERIFIED_EXPOSURE"
        elif in_state or in_checkpoint:
            status="STATE_CHECKPOINT_MISMATCH"
        else:
            status="NOT_RECORDED"
        records.append({"fingerprint":fp,"user":u,"source":source,
                        "state_recorded":in_state,"checkpoint_recorded":in_checkpoint,
                        "status":status,"training_exposure_proven":False})
    return {"audit_version":"v0.6.29","read_only":True,
            "inputs":{"log":str(log_path),"state":str(state_path),
                      "checkpoint":str(checkpoint_path)},
            "inputs_present":{"log":Path(log_path).exists(),
                              "state":Path(state_path).exists(),
                              "checkpoint":Path(checkpoint_path).exists()},
            "counts":{"trusted_pairs":len(records),"state_fingerprints":len(state),
                      "checkpoint_fingerprints":len(checkpoint),
                      "state_only":len(state-checkpoint),
                      "checkpoint_only":len(checkpoint-state),
                      "orphan_state_fingerprints":len(state-observed),
                      "orphan_checkpoint_fingerprints":len(checkpoint-observed)},
            "records":records,
            "warning":"Old fingerprints cannot prove gradient updates or training-set exposure. Do not automatically reset/retrain."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--chat-data",default="data/chat_history.jsonl")
    p.add_argument("--state",default="data/chat_learning_state.json")
    p.add_argument("--checkpoint",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--output",default="results/online_learning_audit_v0629.json")
    args=p.parse_args()
    report=audit(args.chat_data,args.state,args.checkpoint)
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"counts":report["counts"],"output":str(out),
                      "warning":report["warning"]},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
