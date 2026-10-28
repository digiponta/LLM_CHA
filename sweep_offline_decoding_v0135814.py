"""v0.13.58.14: offline decoding sweep with auditable token choices.

Reimplements model.py LanguageModel.generate policy exactly for greedy and
temperature/top-k sampling, including repetition penalty. No network/training.
Read-only checkpoints; output JSON is experimental, never release approval.
"""
import argparse,hashlib,json
from pathlib import Path
from compare_literature_generation_v01356 import PROMPTS

SETTINGS={"greedy":{"temperature":0.0,"top_k":None},
          "topk20":{"temperature":0.6,"top_k":20},
          "topk5":{"temperature":0.6,"top_k":5},
          "temp03":{"temperature":0.3,"top_k":20},
          "temp10":{"temperature":1.0,"top_k":20}}

def adjusted_logits(logits,generated,penalty):
    logits=logits.clone()
    if penalty!=1.0:
        for idx in set(generated):
            if 0<=idx<logits.numel():
                if logits[idx]>=0:logits[idx]/=penalty
                else:logits[idx]*=penalty
    return logits

def choose(logits,temperature,top_k):
    import torch
    if temperature<=0:return int(torch.argmax(logits).item())
    scaled=logits/temperature
    if top_k is not None and 0<top_k<scaled.numel():
        values,ids=torch.topk(scaled,top_k)
        p=torch.softmax(values,dim=-1)
        return int(ids[torch.multinomial(p,1)].item())
    return int(torch.multinomial(torch.softmax(scaled,dim=-1),1).item())

def decode_steps(model,tok,prompt,mode,seed,max_new_tokens=40,penalty=1.10,trace_steps=8):
    import torch
    if max_new_tokens<1 or trace_steps<0:raise ValueError("invalid generation length")
    temperature=mode["temperature"];top_k=mode["top_k"]
    prefix=tok.encode(prompt,add_bos=True)
    if not prefix:raise ValueError("empty prefix")
    generated=list(prefix);trace=[]
    device=next(model.parameters()).device
    torch.manual_seed(seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
    with torch.no_grad():
        for i in range(max_new_tokens):
            context=generated[-model.context_length:]
            tensor=torch.tensor([context],device=device,dtype=torch.long)
            raw=model(tensor)[0,-1,:]
            logits=adjusted_logits(raw,generated,penalty)
            # The top five are ranked under the exact decision distribution,
            # i.e. repetition penalty -> temperature -> top-k truncation.
            decision=logits/temperature if temperature>0 else logits
            if temperature>0 and top_k is not None and 0<top_k<decision.numel():
                vals,indices=torch.topk(decision,top_k)
                masked=torch.full_like(decision,float("-inf"))
                masked[indices]=vals
                decision=masked
            probabilities=torch.softmax(decision,dim=-1)
            topvals,topids=torch.topk(probabilities,min(5,probabilities.numel()))
            chosen=choose(logits,temperature,top_k)
            if i<trace_steps:
                trace.append({"step":i,"chosen_id":chosen,
                   "chosen_text":tok.decode([chosen],skip_special_tokens=False),
                   "chosen_probability":float(probabilities[chosen].item()),
                   "chosen_rank":int((probabilities>probabilities[chosen]).sum().item())+1,
                   "top5":[{"id":int(idx),"text":tok.decode([int(idx)],skip_special_tokens=False),
                            "probability":float(prob)} for idx,prob in zip(topids.tolist(),topvals.tolist())]})
            generated.append(chosen)
            if chosen==tok.eos_id:break
    emitted=generated[len(prefix):]
    return {"text":tok.decode(emitted,skip_special_tokens=True),
            "generated_tokens":len(emitted),"empty":not tok.decode(emitted,skip_special_tokens=True).strip(),
            "trace":trace}
def run(paths,tokenizer,out,max_new_tokens=40,trace_steps=8,seed=135814,selected=None):
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    if out.exists():raise FileExistsError("refusing overwrite")
    tok=Tokenizer.load(str(tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    models={}
    for name,p in paths.items():
        model,_=LanguageModel.load_checkpoint(str(p),device=device)
        if model.vocab_size!=tok.vocab_size:raise ValueError(name+": vocabulary mismatch")
        models[name]=model.eval()
    cases=[]
    for index,case in enumerate(selected if selected is not None else PROMPTS):
        outputs={}
        for name,model in models.items():
            outputs[name]={}
            for key,mode in SETTINGS.items():
                outputs[name][key]=decode_steps(model,tok,case["prompt"],mode,seed+index,
                      max_new_tokens=max_new_tokens,trace_steps=trace_steps)
        cases.append({"id":case["id"],"category":case["category"],"prompt":case["prompt"],
                      "outputs":outputs})
    result={"version":"v0.13.58.14","status":"OFFLINE_DECODING_SWEEP",
            "modes":SETTINGS,"device":str(device),"cases":cases,
            "input_sha256":{**{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()},
                            "tokenizer":hashlib.sha256(tokenizer.read_bytes()).hexdigest()},
            "settings":{"max_new_tokens":max_new_tokens,"trace_steps":trace_steps,
                        "seed":seed,"repetition_penalty":1.10},
            "notes":["greedy top-5 represents softmax of post-penalty logits; selection is argmax",
                     "top-k top-5 is the truncated sampling distribution, not unfiltered model probabilities",
                     "byte-level BPE single-token decoded text may be incomplete UTF-8",
                     "matched seeds do not guarantee matching draws for different distributions",
                     "seven prompts are exploratory; generation is raw LM, not full runtime"],
            "automatic_winner":None,"quality_gate_run":False,
            "human_review_complete":False,"independent_holdout_verified":False,
            "production_promotion_allowed":False}
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
    return result
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    for arm in "ABC":
        ap.add_argument("--"+arm.lower(),type=Path,default=Path(f"results/offline_replay_v0135811/candidate_{arm}.pt"))
    ap.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    ap.add_argument("--output",type=Path,default=Path("results/offline_decoding_sweep_v0135814.json"))
    ap.add_argument("--max-new-tokens",type=int,default=40)
    ap.add_argument("--trace-steps",type=int,default=8)
    ap.add_argument("--seed",type=int,default=135814)
    a=ap.parse_args()
    if a.max_new_tokens<1 or not 0<=a.trace_steps<=a.max_new_tokens:ap.error("invalid steps")
    paths={"base":a.base,"A":a.a,"B":a.b,"C":a.c}
    inputs=[*paths.values(),a.tokenizer]
    for p in inputs:
        if not p.is_file():ap.error("missing input "+str(p))
    if len({p.resolve() for p in inputs+[a.output]})!=len(inputs)+1:ap.error("overlapping paths")
    r=run(paths,a.tokenizer,a.output,a.max_new_tokens,a.trace_steps,a.seed)
    print(json.dumps({"status":r["status"],"cases":len(r["cases"]),
             "models":list(paths),"decoding_modes":list(SETTINGS),
             "automatic_winner":None},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
