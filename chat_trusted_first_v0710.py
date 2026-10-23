"""Interactive trust-first experiment: Approved Memory -> Candidate Adapter on UNKNOWN.

Approval is defined only by an exact match in Approved Memory in this pilot;
the existing chat.py Truth Gate is not bypassed or modified.
"""
import argparse
from pathlib import Path
import torch
from dual_semantic_memory_v071 import DualMemory
from trusted_first_router_v0710 import RouteResult,trusted_first
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from dual_adapters_v073 import DualAdapterModel
from evaluate_dual_adapter_v074 import load_experimental
from dual_inference_v075 import generate

def make_routes(memory,model,tokenizer,max_new_tokens=32):
    def approved_ask(question):
        found=memory.lookup_approved(question)
        if found:
            return RouteResult("ANSWER",found["answer"],found["source_id"],found["id"])
        return RouteResult("UNKNOWN")
    def experimental_ask(question):
        output=generate(model,tokenizer,question,"experimental",max_new_tokens)
        if not output:return RouteResult("UNKNOWN")
        return RouteResult("ANSWER",output,"experimental-adapter-v0.7.3",
                           "local-sandbox")
    return approved_ask,experimental_ask

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--adapter",default="results/adapter_sweep_v077_full/r16_e30_lr1e-03/experimental-adapter.pt")
    p.add_argument("--allow-experimental",action="store_true")
    p.add_argument("--max-new-tokens",type=int,default=32)
    args=p.parse_args()
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(args.base,device=device)
    tokenizer=Tokenizer.load(args.tokenizer)
    if base.vocab_size!=tokenizer.vocab_size:raise ValueError("tokenizer mismatch")
    saved=torch.load(args.adapter,map_location="cpu",weights_only=True)
    model=DualAdapterModel(base,rank=int(saved["rank"])).to(device)
    load_experimental(model,args.adapter)
    memory=DualMemory(args.approved,args.candidates)
    primary,secondary=make_routes(memory,model,tokenizer,args.max_new_tokens)
    print("Trust-first pilot: approved exact match -> UNKNOWN -> experimental fallback")
    print("Experimental fallback enabled:",args.allow_experimental)
    print("Type /exit to quit.")
    while True:
        try:question=input("You> ").strip()
        except (EOFError,KeyboardInterrupt):break
        if question=="/exit":break
        if not question:continue
        result=trusted_first(question,primary,secondary,
                             allow_experimental=args.allow_experimental)
        print("AI>",result["answer"])
        print("[route={}, truth_state={}, source={}, auto_promote={}]".format(
              result["route"],result["truth_state"],result["source"],result["auto_promote"]))
if __name__=="__main__":main()
