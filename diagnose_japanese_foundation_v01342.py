"""v0.13.42 Japanese foundation continuation diagnostic (read-only).

Input is a user-curated UTF-8 TXT file with one independent sentence per line.
Do NOT use train material as validation; --split-label is descriptive only.
Continuations use actual BPE token prefixes, never textual slicing.
"""
import argparse
import hashlib
import json
import random
import re
from pathlib import Path

PREFIXES=(0,4,12,24)

def load_sentences(path,min_chars=28,max_chars=240):
    lines=Path(path).read_text(encoding="utf-8-sig").splitlines()
    seen=set();found=[]
    for line in lines:
        s=line.strip()
        if not (min_chars<=len(s)<=max_chars):continue
        if s.startswith(("#","//","<","{","[")):continue
        if "�" in s or "\t" in s:continue
        if not re.search(r"[。！？!?]$",s):continue
        if s in seen:continue
        seen.add(s);found.append(s)
    return found

def case_prefixes(tokenizer,sentence,lengths=PREFIXES):
    ids=tokenizer.encode(sentence)
    return [(n,ids[:n],ids[n:]) for n in lengths if n<len(ids)]

def char3_overlap(a,b):
    def grams(s):
        s=re.sub(r"\s+","",s)
        return {s[i:i+3] for i in range(max(0,len(s)-2))}
    x,y=grams(a),grams(b)
    if not x and not y:return 1.0
    return len(x&y)/len(x|y) if x|y else 0.0

def trigram_repeat(s):
    s=re.sub(r"\s+","",s)
    items=[s[i:i+3] for i in range(max(0,len(s)-2))]
    return (len(items)-len(set(items)))/len(items) if items else 0.0

def generate(model,tokenizer,prefix,limit,seed,temperature):
    import torch
    import torch.nn.functional as F
    torch.manual_seed(seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
    device=next(model.parameters()).device
    history=[tokenizer.bos_id]+list(prefix)
    produced=[]; stop="limit"
    with torch.no_grad():
        for _ in range(limit):
            logits=model(torch.tensor([history[-model.context_length:]],dtype=torch.long,device=device))[0,-1,:]
            if temperature==0:
                token=int(logits.argmax())
            else:
                vals,ix=torch.topk(logits/temperature,k=min(20,logits.numel()))
                token=int(ix[torch.multinomial(F.softmax(vals,dim=-1),1)].item())
            if token==tokenizer.eos_id:
                stop="eos";break
            if token in (tokenizer.pad_id,tokenizer.bos_id):
                stop="special";break
            history.append(token);produced.append(token)
    return tokenizer.decode(produced),stop,len(produced)

def summarise(details):
    result={}
    for n in PREFIXES:
        for mode in ("greedy","sample"):
            r=[x for x in details if x["prefix_tokens"]==n and x["mode"]==mode]
            if not r:continue
            result[f"{n}:{mode}"]={"cases":len(r),"mean_reference_char3_jaccard":sum(x["reference_char3_jaccard"] for x in r)/len(r),
                                   "mean_repetition":sum(x["repetition"] for x in r)/len(r),
                                   "eos_rate":sum(x["stop"]=="eos" for x in r)/len(r),
                                   "empty_rate":sum(not x["continuation"].strip() for x in r)/len(r),
                                   "mean_new_tokens":sum(x["new_tokens"] for x in r)/len(r)}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,required=True,help="independent sentence-per-line Japanese heldout TXT")
    p.add_argument("--model",type=Path,default=Path("results/rpc_sweep_v01336/rpc_candidate_100000.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/japanese_foundation_continuation_v01342.json"))
    p.add_argument("--split-label",default="USER_ATTESTED_HELDOUT")
    p.add_argument("--limit",type=int,default=32)
    p.add_argument("--seed",type=int,default=1342)
    p.add_argument("--max-new-tokens",type=int,default=48)
    a=p.parse_args()
    if a.limit<1 or a.max_new_tokens<1:p.error("limits must be positive")
    for path in (a.data,a.model,a.tokenizer):
        if not path.is_file():p.error(f"missing file: {path}")
    if a.output.exists():p.error("report already exists")
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    import torch
    pool=load_sentences(a.data)
    if len(pool)<a.limit:p.error(f"only {len(pool)} eligible sentences, need {a.limit}; prepare clean heldout TXT")
    rng=random.Random(a.seed);rng.shuffle(pool)
    chosen=pool[:a.limit]
    tokenizer=Tokenizer.load(str(a.tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(str(a.model),device=device)
    model.eval()
    details=[]
    for i,sentence in enumerate(chosen):
        for n,prefix,reference_ids in case_prefixes(tokenizer,sentence):
            original_prefix=tokenizer.decode(prefix)
            reference=tokenizer.decode(reference_ids)
            for mode,temp in (("greedy",0.0),("sample",0.7)):
                continuation,stop,tokens=generate(model,tokenizer,prefix,a.max_new_tokens,a.seed+i*101+n*7+(mode=="sample"),temp)
                details.append({"case":i,"source_sentence":sentence,"prefix_tokens":n,
                                "prefix":original_prefix,"reference_continuation":reference,
                                "mode":mode,"continuation":continuation,"stop":stop,"new_tokens":tokens,
                                "reference_char3_jaccard":char3_overlap(continuation,reference),
                                "repetition":trigram_repeat(continuation)})
    digest=hashlib.sha256(a.data.read_bytes()).hexdigest()
    report={"version":"v0.13.42","task":"JAPANESE_FOUNDATION_CONTINUATION",
            "split_label":a.split_label,"split_independence_verified":False,
            "dataset_sha256":digest,"data":str(a.data),"model":str(a.model),
            "tokenizer":str(a.tokenizer),"summary":summarise(details),"details":details,
            "production_unchanged":True,
            "limitations":["Input corpus independence is not automatically verified; user must audit provenance.",
                           "Character overlap, EOS and repetition are diagnostics, not human-rated fluency.",
                           "Zero-token condition starts from BOS; longer conditions use gold BPE prefixes.",
                           "Model and tokenizer are frozen, no training or knowledge approval."]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2))
    print("report:",a.output)

if __name__=="__main__":main()
