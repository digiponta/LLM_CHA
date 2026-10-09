"""v0.2.13 checkpoint-matched Japanese and context-utility diagnostics.

Assistant-token NLL uses the same immutable held-out pairs for every checkpoint.
Context delta = (answer NLL without previous turns) - (answer NLL with context).
Positive values indicate improved likelihood of the reference answer WITH context.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer

def last_user_only(prompt):
    return "人: "+prompt.rsplit("人: ",1)[-1]

def score_answer(model,tokenizer,user,answer):
    prefix=user+"\nAI: "
    p=tokenizer.encode(prefix)
    y=tokenizer.encode(answer,add_eos=True)
    if not p or not y:return None
    # Teacher-force the target and keep its token losses separate from the prompt.
    capacity=model.context_length
    if len(y)>=capacity:return None
    context=p[-(capacity-len(y)):]
    tokens=context+y
    if len(tokens)<2:return None
    x=torch.tensor([tokens[:-1]],dtype=torch.long,device=next(model.parameters()).device)
    with torch.inference_mode():
        logits=model(x)[0]
        start=len(context)-1
        loss=F.cross_entropy(logits[start:start+len(y)],torch.tensor(y,device=x.device),reduction="sum")
    return float(loss.item()),len(y)

def summarize(model,tokenizer,rows,max_rows):
    sums={"with":0.,"without":0.,"tokens":0,"count":0,"skipped":0,"improved":0}
    for row in rows[:max_rows]:
        if not isinstance(row.get("user"),str) or not isinstance(row.get("assistant"),str):
            sums["skipped"]+=1;continue
        with_ctx=score_answer(model,tokenizer,row["user"],row["assistant"])
        no_ctx=score_answer(model,tokenizer,last_user_only(row["user"]),row["assistant"])
        if with_ctx is None or no_ctx is None:
            sums["skipped"]+=1;continue
        a,n=with_ctx;b,_=no_ctx
        sums["with"]+=a;sums["without"]+=b;sums["tokens"]+=n
        sums["count"]+=1
        if b>a:sums["improved"]+=1
    n=sums["tokens"]
    if not n:raise ValueError("No evaluable rows")
    c=sums["count"]
    return {"rows":c,"skipped":sums["skipped"],"assistant_tokens":n,
            "nll_with_context":round(sums["with"]/n,5),
            "nll_without_context":round(sums["without"]/n,5),
            "context_gain":round((sums["without"]-sums["with"])/n,5),
            "context_better_fraction":round(sums["improved"]/c,5),
            "perplexity_with_context":round(math.exp(min(30,sums["with"]/n)),4)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",nargs="+",default=[
        "model/model-llm-cha-quality-v028.pt",
        "model/model-llm-cha-dialogue-v0211.pt",
        "model/model-llm-cha-generalization-v0212.pt"])
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--dataset",default="data/dialogue_generalization_v0212/test.jsonl")
    p.add_argument("--max-rows",type=int,default=200)
    p.add_argument("--device",default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--output",default="results/model_diagnostic_v0213.json")
    a=p.parse_args()
    if a.max_rows<1:raise ValueError("max-rows must be positive")
    dataset=Path(a.dataset)
    rows=[json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    tokenizer=Tokenizer.load(a.tokenizer)
    output={}
    for path in a.models:
        model,checkpoint=LanguageModel.load_checkpoint(path,torch.device(a.device))
        model.eval()
        output[path]=summarize(model,tokenizer,rows,a.max_rows)
        del model
        if a.device.startswith("cuda"):torch.cuda.empty_cache()
    report={"dataset":str(dataset),"max_rows":a.max_rows,"device":a.device,
            "results":output,"note":"Reference answer likelihood only, not generated answer quality. Ensure same tokenizer/checkpoint architecture."}
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
