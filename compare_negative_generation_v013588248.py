"""Paired deterministic generation evaluation for negative-only candidates."""
import argparse
import json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from chat import generate_reply
from online_train import ConversationDataset, masked_loss
from train_negative_only_v013588247 import read_negative_signals
from rejection_reuse_v013588246 import normalize_concept_query

def evaluate_case(model,tok,prompt,seed,max_new_tokens,temperature):
    result=generate_reply(model,tok,prompt,max_new_tokens,temperature,0,1.0,seed=seed)
    return {"text":result.text,"token_count":result.token_count,"mean_confidence":result.mean_confidence}

def negative_nll(model,tok,question,answer):
    ds=ConversationDataset([(question,answer)],tok,model.context_length)
    x,y,m=ds[0]
    device=next(model.parameters()).device
    with torch.no_grad():
        return float(masked_loss(model,x.unsqueeze(0).to(device),y.unsqueeze(0).to(device),m.unsqueeze(0).to(device)).item())

def run(base_path,candidate_path,tokenizer_path,negative_data,output,seed=42,max_new_tokens=96):
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=device)
    candidate,_=LanguageModel.load_checkpoint(str(candidate_path),device=device)
    tok=Tokenizer.load(str(tokenizer_path))
    if base.vocab_size!=tok.vocab_size or candidate.vocab_size!=tok.vocab_size:
        raise ValueError("TOKENIZER_MODEL_MISMATCH")
    base.eval();candidate.eval()
    negatives=read_negative_signals(negative_data)
    if not negatives:raise ValueError("NO_NEGATIVES_TO_TEST")
    # Chat-model prompt matches normal standalone generation rather than GUI's
    # evidence-aware prompt. Explicitly report this limitation.
    cases=[{"name":"negative_"+str(i+1),"question":row["question"],"rejected":row["rejected_answer"]}
           for i,row in enumerate(negatives)]
    cases += [{"name":"CPU","question":"CPUとは","rejected":None},
              {"name":"GPU","question":"GPUとは","rejected":None},
              {"name":"cosmos_paraphrase","question":normalize_concept_query("宇宙を説明してください")+"とは","rejected":None}]
    results=[]
    for case in cases:
        prompt="人: "+case["question"]+"\nAI: "
        before=evaluate_case(base,tok,prompt,seed,max_new_tokens,0.0)
        after=evaluate_case(candidate,tok,prompt,seed,max_new_tokens,0.0)
        row={"name":case["name"],"question":case["question"],"prompt":prompt,
            "base":before,"candidate":after,"changed":before["text"]!=after["text"]}
        if case["rejected"]:
            row["rejected_answer"]=case["rejected"]
            row["base_negative_nll"]=negative_nll(base,tok,case["question"],case["rejected"])
            row["candidate_negative_nll"]=negative_nll(candidate,tok,case["question"],case["rejected"])
            row["rejected_exact_repeat_base"]=before["text"].strip()==case["rejected"].strip()
            row["rejected_exact_repeat_candidate"]=after["text"].strip()==case["rejected"].strip()
        results.append(row)
    report={"status":"PAIRED_GENERATION_DIAGNOSTIC","base_model":str(base_path),"candidate_model":str(candidate_path),
            "seed":seed,"decoding":"greedy","max_new_tokens":max_new_tokens,
            "cases":results,"production_promoted":False,
            "limitations":["Prompt is standalone 人: ... AI:, not GUI Wikipedia-conditioned prompt.",
                           "Greedy generation comparison alone cannot establish knowledge retention.",
                           "No automatic approval or production model update."]}
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--candidate",default="results/negative_only_v013588247_steps3.candidate.pt")
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--negative-data",default="data/negative_teacher_signals_v013588244.jsonl")
    p.add_argument("--output",default="results/negative_generation_eval_v013588248.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--max-new-tokens",type=int,default=96)
    a=p.parse_args()
    report=run(a.base,a.candidate,a.tokenizer,a.negative_data,a.output,a.seed,a.max_new_tokens)
    print(json.dumps({"status":report["status"],"cases":len(report["cases"]),
        "changed":sum(x["changed"] for x in report["cases"]),
        "output":a.output,"production_promoted":False},ensure_ascii=False))
if __name__=="__main__":main()
