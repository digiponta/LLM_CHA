"""v0.2.33.12: read-only core LLM architecture audit.

Verify checkpoint positional configuration and observable response sensitivity to
order changes of prompt tokens. No model or memory modifications.
"""
import argparse,json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer

def order_sensitivity(model,first,second):
    """Same multiset, same last token. Causal stacks can still encode order
    indirectly via earlier contextual states; this is an empirical probe, not
    a mathematical proof of impossibility."""
    model.eval()
    device=next(model.parameters()).device
    a=torch.tensor([first],dtype=torch.long,device=device)
    b=torch.tensor([second],dtype=torch.long,device=device)
    with torch.inference_mode():
        logits_a=model(a)[0,-1].float()
        logits_b=model(b)[0,-1].float()
    return {"max_abs_logit_delta":float((logits_a-logits_b).abs().max()),
            "mean_abs_logit_delta":float((logits_a-logits_b).abs().mean()),
            "top1_a":int(logits_a.argmax()),"top1_b":int(logits_b.argmax())}

def audit_checkpoint(model_path,tokenizer_path):
    tokenizer=Tokenizer.load(tokenizer_path)
    model,checkpoint=LanguageModel.load_checkpoint(model_path,torch.device("cpu"))
    if tokenizer.vocab_size!=model.vocab_size:raise ValueError("Vocab mismatch")
    cfg=model.config()
    text_a="赤い本を机に置きます。"
    text_b="青い箱を棚に運びます。"
    # Token IDs from first 4 positions are permuted; preserve the final query.
    ids=tokenizer.encode(text_a,add_bos=True)
    if len(ids)<5:raise ValueError("Insufficient prompt token IDs for order probe")
    perm=list(ids)
    perm[1:4]=list(reversed(perm[1:4]))
    model.eval()
    token_order=order_sensitivity(model,ids,perm)
    result={"model":model_path,"tokenizer":tokenizer_path,
        "config":cfg,"checkpoint_epoch":checkpoint.get("epoch"),
        "checkpoint_loss":checkpoint.get("loss"),
        "position_embedding_present":model.position_embedding is not None,
        "causal_attention":all(block.attention.causal for block in model.blocks),
        "order_probe":{"original_token_ids":ids,"permuted_token_ids":perm,**token_order},
        "implementation_flags":{
           "generate_repetition_penalizes_prompt_tokens":True,
           "generate_resets_position_indices_for_sliding_context":True,
           "train_response_only_targets_aligned_by_separate_encode":True},
        "interpretation":{
          "no_position_embedding":"WARNING: explicitly learned absolute positions are absent; causal network may still encode some indirect order context",
          "order_test":"Single finite permutation probe does not establish global order sensitivity or copying ability",
          "repetition_penalty":"Prompt IDs are included in penalty set; can disfavor literal copying",
          "status":"CODE_AND_CHECKPOINT_INSPECTION_NOT_A_FUNCTIONAL_FIX"}}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--copy",default="model/model-llm-cha-copy-v02339.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--out",default="results/core_architecture_audit_v023312.json")
    a=p.parse_args()
    path=Path(a.out)
    if path.exists():raise FileExistsError(f"Refusing overwrite: {path}")
    results={key:audit_checkpoint(value,a.tokenizer)
             for key,value in (("base",a.base),("copy",a.copy))}
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"version":"v0.2.33.12",
      "read_only":True,"no_training":True,"results":results},
      ensure_ascii=False,indent=2),encoding="utf-8")
    for key,res in results.items():
        print(f"[{key}] config:",res["config"])
        print(" position_embedding_present:",res["position_embedding_present"])
        print(" causal_attention:",res["causal_attention"])
        print(" ordering:",res["order_probe"]["max_abs_logit_delta"],
                            res["order_probe"]["mean_abs_logit_delta"])
    print("Saved",path)
if __name__=="__main__":main()
