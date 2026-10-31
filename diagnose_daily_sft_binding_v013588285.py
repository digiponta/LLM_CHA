"""Read-only diagnostic: why the same trusted pairs are retrained.

The current trainer requires each pair's fingerprint in BOTH the loaded
base checkpoint metadata and the training state. It intentionally rebinds
if either is absent, so rerunning against the original base will retrain.
"""
import argparse,json
from pathlib import Path
from online_train import (load_chat_jsonl,deduplicate_trusted_rows,
                          pair_fingerprint,load_training_state,
                          checkpoint_trained_fingerprints)

def diagnose(chat_data,state,base_model,candidate_model):
    rows=deduplicate_trusted_rows(load_chat_jsonl(Path(chat_data)))
    state_ids=load_training_state(Path(state))
    base_ids=checkpoint_trained_fingerprints(Path(base_model))
    candidate_ids=checkpoint_trained_fingerprints(Path(candidate_model))
    fp={pair_fingerprint(user,answer) for user,answer,_ in rows}
    # Same policy as online_train.py: OR, not AND.
    base_rebind=fp-base_ids | fp-state_ids
    candidate_rebind=fp-candidate_ids | fp-state_ids
    return {
        "status":"SFT_BINDING_DIAGNOSTIC",
        "trusted_unique":len(fp),
        "present_in_state":len(fp & state_ids),
        "present_in_original_base":len(fp & base_ids),
        "present_in_candidate":len(fp & candidate_ids),
        "retrain_if_original_base":len(base_rebind),
        "retrain_if_candidate_base":len(candidate_rebind),
        "reason":"Trainer requires fingerprints in base checkpoint AND state",
        "production_changed":False,
        "model_changed":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--chat-data",default="data/daily_sft_train_v013588284.jsonl")
    p.add_argument("--state",default="results/daily-sft-state-v013588284.json")
    p.add_argument("--base-model",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--candidate-model",default="model/daily-sft-candidate-v013588284.pt")
    p.add_argument("--output",default="results/daily_sft_binding_diagnostic_v013588285.json")
    a=p.parse_args()
    paths=(a.chat_data,a.state,a.base_model,a.candidate_model)
    absent=[x for x in paths if not Path(x).exists()]
    if absent:raise FileNotFoundError("Missing input: "+", ".join(absent))
    result=diagnose(*paths)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
