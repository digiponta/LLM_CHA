"""v0.13.35 read-only RPC validation free-generation A/B evaluation."""
import argparse,json,re,random
from pathlib import Path
import torch
from chat import generate_reply
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from online_train import USER_PREFIX,AI_PREFIX
from train_rpc_dialogue_sft_v01334 import read_rows

def repetition(text):
    s=re.sub(r"\s+","",text)
    windows=[s[i:i+3] for i in range(max(0,len(s)-2))]
    return (len(windows)-len(set(windows)))/len(windows) if windows else 0.0

def summarize(rows):
    n=len(rows)
    return {"cases":n,"exact_match":sum(x["exact_match"] for x in rows),
            "mean_repetition":sum(x["repetition"] for x in rows)/n if n else None,
            "mean_tokens":sum(x["generated_tokens"] for x in rows)/n if n else None,
            "empty":sum(not x["text"].strip() for x in rows)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,default=Path("results/rpc_sft_full_v01333/rpc_sft_val_v01333.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--candidate",type=Path,default=Path("results/rpc_sft_candidate_v01334.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/rpc_free_generation_v01335.json"))
    p.add_argument("--limit",type=int,default=24)
    p.add_argument("--max-new-tokens",type=int,default=64)
    a=p.parse_args()
    if a.limit<1 or a.max_new_tokens<1:p.error("positive limits required")
    if a.output.exists():p.error("output exists; specify another filename")
    for path in (a.data,a.base,a.candidate,a.tokenizer):
        if not path.exists():p.error(f"missing {path}")
    rows=read_rows(a.data,0)
    # Sample across validation dialogues instead of first consecutive samples.
    by_dialogue={}
    for row in rows:
        by_dialogue.setdefault(str(row["dialogue_id"]),[]).append(row)
    rng=random.Random(1335)
    keys=sorted(by_dialogue)
    rng.shuffle(keys)
    probes=[]
    for key in keys:
        choices=by_dialogue[key]
        probes.append(choices[len(choices)//2])
        if len(probes)>=a.limit:break
    if len(probes)<a.limit:
        extra=[r for r in rows if r not in probes]
        rng.shuffle(extra)
        probes.extend(extra[:a.limit-len(probes)])
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer=Tokenizer.load(str(a.tokenizer))
    details={};summary={}
    for name,path in (("BASE",a.base),("RPC_SFT",a.candidate)):
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        model.eval();results=[]
        with torch.no_grad():
            for r in probes:
                prompt=f"{USER_PREFIX}{r['user']}\n{AI_PREFIX}"
                gen=generate_reply(model,tokenizer,prompt,a.max_new_tokens,0,20,1.0)
                result={"dialogue_id":r["dialogue_id"],"utterance_id":r["utterance_id"],
                        "prompt":r["user"],"reference":r["assistant"],
                        "text":gen.text,"generated_tokens":gen.token_count,
                        "exact_match":gen.text.strip()==r["assistant"].strip(),
                        "repetition":repetition(gen.text)}
                results.append(result)
        details[name]=results;summary[name]=summarize(results)
    report={"version":"v0.13.35","source":"VALIDATION_NOT_TEST",
            "same_probes":True,"greedy":True,"production_unchanged":True,
            "summary":summary,"details":details,
            "limitations":"Exact match is not semantic correctness; topic relevance requires human review."}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2));print("report:",a.output)
if __name__=="__main__":main()
