"""v0.7.4 comparison of frozen Base, Trusted and Experimental adapters.

Teacher-forced answer-token metrics, NOT free-form conversational accuracy.
No writes to the model or knowledge stores.
"""
import argparse
import json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from online_train import ConversationDataset
from dual_adapters_v073 import DualAdapterModel,masked_cross_entropy,frozen_digest
from dual_semantic_memory_v071 import DualMemory

def load_experimental(model,path):
    checkpoint=torch.load(path,map_location="cpu",weights_only=True)
    if checkpoint.get("format")!="llm-cha-experimental-adapter-v0.7.3":
        raise ValueError("unsupported experimental adapter format")
    if checkpoint.get("route")!="experimental" or checkpoint.get("approved") is not False or checkpoint.get("trusted_deployable") is not False:
        raise ValueError("adapter trust boundary violated")
    if checkpoint.get("rank")!=model.experimental.down.out_features:
        raise ValueError("adapter rank mismatch")
    if checkpoint.get("base_hash")!=frozen_digest(model.base):
        raise ValueError("base checkpoint hash mismatch")
    model.experimental.load_state_dict(checkpoint["adapter"],strict=True)
    return checkpoint

@torch.no_grad()
def evaluate_pairs(model,tokenizer,pairs,device):
    dataset=ConversationDataset(pairs,tokenizer,model.base.context_length)
    metrics={}
    model.eval()
    for route in ("base","trusted","experimental"):
        token_loss=0.0
        token_count=0
        correct=0
        for i in range(len(dataset)):
            x,y,mask=(v.unsqueeze(0).to(device) for v in dataset[i])
            if route=="base": logits=model.base(x)
            else: logits=model(x,route=route)
            counts=mask.sum().item()
            token_loss+=float(masked_cross_entropy(logits,y,mask).item())*counts
            correct+=int(((logits.argmax(dim=-1)==y)&(mask>0)).sum().item())
            token_count+=int(counts)
        metrics[route]={"tokens":token_count,
            "mean_nll":token_loss/max(1,token_count),
            "teacher_forced_token_top1":correct/max(1,token_count)}
    return metrics

def run(base_path,tokenizer_path,approved_path,candidate_path,adapter_path,report_path,
        max_protected=20):
    paths=[Path(x).resolve() for x in (base_path,tokenizer_path,approved_path,candidate_path,adapter_path)]
    report_path=Path(report_path).resolve()
    if report_path in paths:raise ValueError("report overlaps protected file")
    memory=DualMemory(approved_path,candidate_path)
    pending=[r for r in memory.candidates() if r["status"]=="PENDING"]
    if not pending:raise ValueError("no pending candidates")
    approved=memory.approved()[:max_protected]
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if tokenizer.vocab_size!=base.vocab_size:raise ValueError("tokenizer mismatch")
    # Inspection of checkpoint rank is safe only for trusted local files.
    saved=torch.load(adapter_path,map_location="cpu",weights_only=True)
    model=DualAdapterModel(base,rank=int(saved["rank"])).to(device)
    load_experimental(model,adapter_path)
    candidate_metrics=evaluate_pairs(model,tokenizer,[(r["question"],r["answer"]) for r in pending],device)
    protected_metrics=(evaluate_pairs(model,tokenizer,
        [(r["question"],r["answer"]) for r in approved],device) if approved else None)
    result={"version":"v0.7.4","device":str(device),
        "evaluation":"teacher-forced answer-token, not free generation",
        "candidate_count":len(pending),"protected_count":len(approved),
        "candidate":candidate_metrics,"approved_probes":protected_metrics,
        "candidate_nll_delta_experimental_minus_base":candidate_metrics["experimental"]["mean_nll"]-candidate_metrics["base"]["mean_nll"],
        "adapter_is_experimental":True,"approval_granted":False,
        "automatic_promotion":False,"quality_pass":None}
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    ap.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--approved",default="data/approved_v071.jsonl")
    ap.add_argument("--candidates",default="data/candidates_v071.jsonl")
    ap.add_argument("--adapter",default="results/adapter_sandbox_v073/experimental-adapter.pt")
    ap.add_argument("--report",default="results/adapter_quality_v074.json")
    a=ap.parse_args()
    print(json.dumps(run(a.base,a.tokenizer,a.approved,a.candidates,a.adapter,a.report),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
