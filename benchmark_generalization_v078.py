"""v0.7.8 independent paraphrase and protected-retention benchmark.

No training/promotion. Holdouts are externally specified, with exact
train-question overlap rejected. Results are diagnostic, not certification.
"""
import argparse
import json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from dual_adapters_v073 import DualAdapterModel
from evaluate_dual_adapter_v074 import load_experimental
from dual_inference_v075 import generate
from dual_semantic_memory_v071 import DualMemory

DEFAULT_VARIANTS=(
    "v072実験の合言葉を教えてください",
    "v072実験で使う合言葉を答えて",
    "合言葉は何でしたか、v072実験について",
    "v072の実験における合言葉は？",
    "実験v072の合言葉を知りたいです",
)
def norm(text):
    return " ".join(str(text).strip().split())

def make_holdout(candidate):
    """Paraphrase probes are manually authored, not independent facts."""
    if candidate["question"]!="v072実験の合言葉は何ですか":
        raise ValueError("default holdouts only apply to the v072 test candidate")
    return [{"question":question,"reference":candidate["answer"],
             "source_id":candidate["source_id"],"candidate_id":candidate["id"]}
            for question in DEFAULT_VARIANTS]

def validate_holdouts(holdouts,training_questions):
    seen=set()
    training={norm(s) for s in training_questions}
    for item in holdouts:
        if not isinstance(item,dict) or not all(
            isinstance(item.get(k),str) and item[k].strip()
            for k in ("question","reference")):
            raise ValueError("invalid holdout record")
        question=norm(item["question"])
        if question in training:raise ValueError("training question found in holdout")
        if question in seen:raise ValueError("duplicate holdout")
        seen.add(question)
    if not seen:raise ValueError("empty holdout")
    return holdouts

def score(model,tokenizer,rows,max_new_tokens=32):
    cases=[]
    for row in rows:
        outputs={route:generate(model,tokenizer,row["question"],route,max_new_tokens)
                 for route in ("base","trusted","experimental")}
        cases.append({"question":row["question"],"reference":row["reference"],
                      "outputs":outputs,
                      "exact_match":{k:(v==row["reference"].strip()) for k,v in outputs.items()}})
    metric={k:sum(r["exact_match"][k] for r in cases)/len(cases)
            for k in ("base","trusted","experimental")} if cases else None
    return {"count":len(cases),"exact_match":metric,"cases":cases}

def run(base_path,tokenizer_path,approved_path,candidate_path,checkpoint_paths,
        output_path,holdout_path=None,max_new_tokens=32):
    if max_new_tokens<1 or max_new_tokens>128:raise ValueError("invalid token limit")
    protected={Path(p).resolve() for p in
        (base_path,tokenizer_path,approved_path,candidate_path,*checkpoint_paths)}
    output_path=Path(output_path).resolve()
    if output_path in protected:raise ValueError("output overlaps input")
    memory=DualMemory(approved_path,candidate_path)
    pending=[r for r in memory.candidates() if r["status"]=="PENDING"]
    if not pending:raise ValueError("no pending candidates")
    if holdout_path:
        holdouts=json.loads(Path(holdout_path).read_text(encoding="utf-8"))
        if not isinstance(holdouts,list):raise ValueError("holdout JSON must be array")
    else:
        if len(pending)!=1:raise ValueError("default paraphrases require one candidate")
        holdouts=make_holdout(pending[0])
    validate_holdouts(holdouts,[r["question"] for r in pending])
    # Approved knowledge is a separate probe set, not silently approved by benchmark.
    approved=memory.approved()
    protected_rows=[{"question":r["question"],"reference":r["answer"]} for r in approved]
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(base_path),device=device)
    tokenizer=Tokenizer.load(str(tokenizer_path))
    if tokenizer.vocab_size!=base.vocab_size:raise ValueError("tokenizer mismatch")
    results=[]
    for checkpoint_path in checkpoint_paths:
        saved=torch.load(checkpoint_path,map_location="cpu",weights_only=True)
        model=DualAdapterModel(base,rank=int(saved["rank"])).to(device)
        load_experimental(model,checkpoint_path)
        holdout=score(model,tokenizer,holdouts,max_new_tokens)
        retention=score(model,tokenizer,protected_rows,max_new_tokens)
        base_retention=(retention["exact_match"] or {}).get("base")
        experimental_retention=(retention["exact_match"] or {}).get("experimental")
        results.append({"checkpoint":str(checkpoint_path),
          "rank":int(saved["rank"]),"holdout":holdout,"retention":retention,
          "candidate_generalization_improved":
             holdout["exact_match"]["experimental"]>holdout["exact_match"]["base"],
          "retention_nonregression":None if not protected_rows else
             experimental_retention>=base_retention,
          "quality_pass":None if not protected_rows else
             (experimental_retention>=base_retention and
              holdout["exact_match"]["experimental"]>holdout["exact_match"]["base"])})
    output={"version":"v0.7.8","device":str(device),
      "holdout_definition":"untrained question strings; reference answer may be in training",
      "holdout_count":len(holdouts),"approved_count":len(approved),
      "approved_coverage_sufficient":bool(approved),
      "automatic_promotion":False,"production_integration":False,"results":results}
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--holdouts",default=None)
    p.add_argument("--checkpoints",nargs="+",default=[
      "results/adapter_sweep_v077_full/r8_e100_lr3e-04/experimental-adapter.pt",
      "results/adapter_sweep_v077_full/r16_e30_lr1e-03/experimental-adapter.pt",
      "results/adapter_sweep_v077_full/r32_e30_lr1e-03/experimental-adapter.pt"])
    p.add_argument("--report",default="results/generalization_retention_v078.json")
    p.add_argument("--max-new-tokens",type=int,default=32)
    a=p.parse_args()
    result=run(a.base,a.tokenizer,a.approved,a.candidates,a.checkpoints,a.report,a.holdouts,a.max_new_tokens)
    print(json.dumps({"version":result["version"],"device":result["device"],
      "holdout_count":result["holdout_count"],"approved_count":result["approved_count"],
      "results":[{"checkpoint":r["checkpoint"],"holdout":r["holdout"]["exact_match"],
        "retention":r["retention"]["exact_match"],"quality_pass":r["quality_pass"]}
        for r in result["results"]]},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
