"""v0.7.16 first-token rank and probability analysis on held-out paraphrases."""
import argparse
import json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from dual_adapters_v073 import DualAdapterModel
from evaluate_dual_adapter_v074 import load_experimental
from diagnose_generation_v076 import probe

def run(summary_path,base,tokenizer,checkpoint,output):
    summary=json.loads(Path(summary_path).read_text(encoding="utf-8"))
    if summary.get("version")!="v0.7.15":
        raise ValueError("requires v0.7.15 summary")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base_model,_=LanguageModel.load_checkpoint(base,device=device)
    tok=Tokenizer.load(tokenizer)
    ckpt=torch.load(checkpoint,map_location="cpu",weights_only=True)
    model=DualAdapterModel(base_model,rank=int(ckpt["rank"])).to(device)
    load_experimental(model,checkpoint)
    model.eval()
    rows=[]
    for case in summary["holdout_cases"]:
        q=case["question"];reference=case["reference"]
        routes={route:probe(model,tok,q,reference,route) for route in ("base","trusted","experimental")}
        rows.append({"question":q,"reference":reference,"routes":routes,
            "rank_improvement":routes["base"]["first_reference_token_rank"]-routes["experimental"]["first_reference_token_rank"]})
    result={"version":"v0.7.16","device":str(device),"count":len(rows),
            "rank_improved":sum(x["rank_improvement"]>0 for x in rows),
            "cases":rows,"auto_promote":False,
            "note":"Teacher-forced first answer token rank; not a measure of factual truth."}
    dest=Path(output).resolve()
    if dest in {Path(x).resolve() for x in (summary_path,base,tokenizer,checkpoint)}:
        raise ValueError("output overlaps input")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--summary",default="results/multi_fact_v0715/summary_v0715.json")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--checkpoint",default="results/multi_fact_v0715/experimental-adapter.pt")
    p.add_argument("--output",default="results/multi_fact_v0716/token_ranks.json")
    a=p.parse_args()
    result=run(a.summary,a.base,a.tokenizer,a.checkpoint,a.output)
    print(json.dumps({"count":result["count"],"device":result["device"],
                      "rank_improved":result["rank_improved"],"output":a.output},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
