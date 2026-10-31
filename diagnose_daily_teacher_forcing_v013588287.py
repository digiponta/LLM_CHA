"""Read-only tokenwise teacher forcing vs greedy divergence for seen SFT pairs."""
import argparse,json,math
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from chat import build_prompt
from online_train import load_chat_jsonl
from diagnose_daily_decode_v013588286 import PROBES

def first_divergence(reference,generated):
    for i,(a,b) in enumerate(zip(reference,generated)):
        if a!=b:return i
    return min(len(reference),len(generated)) if len(reference)!=len(generated) else None

@torch.no_grad()
def diagnose_one(model,tokenizer,question,answer,max_steps=64):
    prompt,_=build_prompt([],question,0)
    prefix=tokenizer.encode(prompt,add_bos=True)
    targets=tokenizer.encode(answer,add_eos=True)
    device=next(model.parameters()).device
    context_length=model.context_length
    rows=[]
    for i,token in enumerate(targets):
        context=(prefix+targets[:i])[-context_length:]
        logits=model(torch.tensor([context],device=device,dtype=torch.long))[0,-1,:]
        lp=F.log_softmax(logits,dim=-1)
        probability=float(torch.exp(lp[token]))
        rank=int((logits>logits[token]).sum().item())+1
        rows.append({"position":i,"token_id":int(token),"token_text":tokenizer.decode([token],skip_special_tokens=False),
                     "probability":probability,"rank":rank,"nll":float(-lp[token])})
    generated=[]
    for i in range(max_steps):
        context=(prefix+generated)[-context_length:]
        logits=model(torch.tensor([context],device=device,dtype=torch.long))[0,-1,:]
        next_id=int(torch.argmax(logits).item())
        generated.append(next_id)
        if next_id==tokenizer.eos_id:break
        if "\n" in tokenizer.decode(generated,skip_special_tokens=True):break
    diff=first_divergence(targets,generated)
    return {"question":question,"reference":answer,"target_token_count":len(targets),
            "teacher_forced_mean_nll":sum(x["nll"] for x in rows)/len(rows),
            "teacher_forced_top1_count":sum(x["rank"]==1 for x in rows),
            "greedy_first_divergence_position":diff,
            "greedy_text":tokenizer.decode([t for t in generated if t!=tokenizer.eos_id],skip_special_tokens=True),
            "token_details":rows}

def run(model_path,tokenizer,pairs,device):
    model,_=LanguageModel.load_checkpoint(str(model_path),device=device)
    model.eval()
    ref={q:a for q,a,_ in pairs}
    return [diagnose_one(model,tokenizer,q,ref[q]) for q in PROBES]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--candidate",default="model/daily-sft-candidate-v013588284.pt")
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--train",default="data/daily_sft_train_v013588284.jsonl")
    p.add_argument("--output",default="results/daily_teacher_forcing_v013588287.json")
    a=p.parse_args()
    for path in (a.base,a.candidate,a.tokenizer,a.train):
        if not Path(path).is_file():raise FileNotFoundError(path)
    tok=Tokenizer.load(a.tokenizer)
    pairs=load_chat_jsonl(Path(a.train))
    dev=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    result={"status":"TEACHER_FORCED_TOKEN_ANALYSIS","base":run(a.base,tok,pairs,dev),
            "candidate":run(a.candidate,tok,pairs,dev),
            "model_changed":False,"note":"teacher forcing conditions on reference tokens; greedy conditions on its own output"}
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"output":str(out),
       "summary":{k:[{"question":x["question"],"mean_nll":round(x["teacher_forced_mean_nll"],4),
       "top1":x["teacher_forced_top1_count"],"tokens":x["target_token_count"],
       "divergence":x["greedy_first_divergence_position"]} for x in result[k]] for k in ("base","candidate")}},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
