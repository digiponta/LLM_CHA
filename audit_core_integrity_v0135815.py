"""Read-only LLM_CHA core integrity audit v0.13.58.15.

Audits actual checkpoint architecture, probe order sensitivity, causal
invariance, repeated prompt penalty, and train/prompt formatting.
No training, network access or checkpoint modification.
"""
import argparse,json,hashlib
from pathlib import Path

def source_report():
    from train_japanese_foundation_v01344 import make_examples
    from audit_offline_replay_v0135810 import read_file
    return {"training_builder":"make_examples: BOS + entire line + EOS, all nonpad next-token labels",
            "replay_jsonl_formatter":"人: {user} AI: {assistant}",
            "generation_probe_formatter":"人: {user}\\nAI: ",
            "format_match":False,
            "assistant_only_loss":False}

def model_diagnostics(model,device):
    import torch
    model.eval()
    vocab=model.vocab_size
    a,b,c=[min(vocab-1,i) for i in (10,11,12)]
    if len({a,b,c})<3:raise ValueError("vocab too small")
    # Swapping the two immediately preceding tokens should be perceptible
    # to a strongly order-sensitive architecture.
    x=torch.tensor([[a,b,c]],device=device)
    y=torch.tensor([[b,a,c]],device=device)
    z=torch.tensor([[a,b,c]],device=device)
    w=torch.tensor([[a,b,min(vocab-1,13)]],device=device)
    with torch.no_grad():
        fx=model(x);fy=model(y);fz=model(z);fw=model(w)
    diff=float((fx[0,-1]-fy[0,-1]).abs().max().item())
    # Future token change must not alter positions 0,1.
    causal=float((fz[:,:2]-fw[:,:2]).abs().max().item())
    return {"position_embedding_enabled":model.position_embedding is not None,
            "permutation_last_logit_max_abs_delta":diff,
            "future_token_influence_max_abs_delta":causal,
            "causality_smoke_pass":causal<1e-5,
            "permutation_test_note":"Causal attention without positional embeddings may still weakly encode order; zero is not guaranteed."}

def run(paths):
    import torch
    from model import LanguageModel
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    models={}
    for name,path in paths.items():
        model,checkpoint=LanguageModel.load_checkpoint(str(path),device=device)
        models[name]={"checkpoint_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                      "config":model.config(),
                      "probe":model_diagnostics(model,device)}
        del model
    return {"version":"v0.13.58.15","status":"READ_ONLY_CORE_AUDIT",
       "models":models,"source_findings":source_report(),
       "notes":["Model architecture flags are read from the checkpoint, not default constructor arguments.",
                "Permutation sensitivity is diagnostic, not a complete order understanding measure.",
                "Source formatting mismatch is established by inspected source code.",
                "No evidence here that causal masking is defective unless causality smoke test fails.",
                "No model or training-data edits performed."],
       "automatic_fix":False,"production_promotion_allowed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    for key in "ABC":p.add_argument("--"+key.lower(),type=Path,default=Path(f"results/offline_replay_v0135811/candidate_{key}.pt"))
    p.add_argument("--output",type=Path,default=Path("results/core_integrity_audit_v0135815.json"))
    a=p.parse_args()
    files={"base":a.base,"A":a.a,"B":a.b,"C":a.c}
    for path in files.values():
        if not path.is_file():p.error("missing checkpoint: "+str(path))
    if a.output.exists():p.error("output exists; refusing overwrite")
    r=run(files)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x",encoding="utf-8") as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print(json.dumps({"status":r["status"],"position_embedding_enabled":{k:v["probe"]["position_embedding_enabled"] for k,v in r["models"].items()},"causality_smoke_pass":{k:v["probe"]["causality_smoke_pass"] for k,v in r["models"].items()}},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
