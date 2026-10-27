"""v0.13.11: read-only paired checkpoint evaluation.

Training-set fit is NOT holdout generalization. No checkpoint promotion.
"""
import argparse
import json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from online_train import ConversationDataset, masked_loss, load_chat_jsonl, checkpoint_trained_fingerprints

def evaluate_pairs(model, tokenizer, pairs, device):
    if not pairs:
        return None
    ds=ConversationDataset(pairs,tokenizer,model.context_length)
    total=0.0
    weight=0.0
    model.eval()
    with torch.no_grad():
        for x,y,mask in ds:
            x=x.unsqueeze(0).to(device)
            y=y.unsqueeze(0).to(device)
            mask=mask.unsqueeze(0).to(device)
            n=float(mask.sum().item())
            if not n:continue
            total+=float(masked_loss(model,x,y,mask).item())*n
            weight+=n
    return total/weight if weight else None

def compare_metrics(before,after):
    return {"base_nll":before,"candidate_nll":after,
            "delta_nll":round(after-before,6) if before is not None and after is not None else None}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--candidate",type=Path,default=Path("model/model-gpu-v1.6.2-unapproved-pilot-v01310.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--pilot-data",type=Path,default=Path("results/unapproved_pilot_pairs_v01310.jsonl"))
    p.add_argument("--stability-data",type=Path,default=Path("data/stability_replay_v104.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/unapproved_checkpoint_comparison_v01311.json"))
    args=p.parse_args()
    for path in (args.base,args.candidate,args.tokenizer,args.pilot_data):
        if not path.exists():p.error(f"missing input: {path}")
    tokenizer=Tokenizer.load(str(args.tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(args.base),device=device)
    candidate,_=LanguageModel.load_checkpoint(str(args.candidate),device=device)
    if (base.vocab_size,base.context_length)!=(candidate.vocab_size,candidate.context_length):
        p.error("incompatible architectures")
    pilot=[(u,a) for u,a,_ in load_chat_jsonl(args.pilot_data)]
    stability=[(u,a) for u,a,_ in load_chat_jsonl(args.stability_data)]
    report={"version":"v0.13.11","device":str(device),
            "pilot_count":len(pilot),"stability_count":len(stability),
            "pilot_evaluation":"IN_SAMPLE_NOT_INDEPENDENT",
            "stability_evaluation":"REPLAY_NOT_INDEPENDENT",
            "pilot_fit":compare_metrics(evaluate_pairs(base,tokenizer,pilot,device),
                                        evaluate_pairs(candidate,tokenizer,pilot,device)),
            "stability_retention":compare_metrics(evaluate_pairs(base,tokenizer,stability,device),
                                                  evaluate_pairs(candidate,tokenizer,stability,device)),
            "base_fingerprint_count":len(checkpoint_trained_fingerprints(args.base)),
            "candidate_fingerprint_count":len(checkpoint_trained_fingerprints(args.candidate)),
            "approved_status":"NOT_INFERRED_FROM_WEIGHTS",
            "promoted":False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
