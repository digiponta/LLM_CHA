"""v0.13.32 free generation across B_RAW weight variants; read-only."""
import argparse
import json
import re
from pathlib import Path
from compare_free_generation_v01330 import evaluate_one
from train_b_raw_weighted_v01331 import plan

def repetition_ratio(text):
    # Fraction of overlapping repeated 3-character windows; diagnostic heuristic.
    s=re.sub(r"\s+","",text)
    windows=[s[i:i+3] for i in range(max(0,len(s)-2))]
    return (len(windows)-len(set(windows)))/len(windows) if windows else 0.0

def summarize(rows):
    n=len(rows)
    return {"cases":n,
            "exact_text_matches":sum(bool(r["exact_text_match"]) for r in rows),
            "grounded_excerpts":sum(bool(r["grounded_excerpt"]) for r in rows),
            "first_token_matches_reencoded":sum(r["first_divergence_reencoded"] is None or r["first_divergence_reencoded"]>0 for r in rows),
            "mean_repetition_ratio":sum(repetition_ratio(r["raw_generation"]) for r in rows)/n if n else None,
            "mean_generated_tokens":sum(r["generated_tokens"] for r in rows)/n if n else None}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prefix",type=Path,default=Path("results/b_raw_weighted_v01331"))
    p.add_argument("--data",type=Path,default=Path("results/unapproved_b_raw_v01326.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/b_raw_weighted_generation_v01332.json"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--max-new-tokens",type=int,default=96)
    a=p.parse_args()
    if a.limit<1 or a.max_new_tokens<1:p.error("positive limits required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from unapproved_corpus_learning_v0139 import load_jsonl
    if not a.data.exists() or not a.tokenizer.exists():p.error("missing tokenizer or dataset")
    rows=load_jsonl(a.data)[:a.limit]
    if not rows:p.error("empty dataset")
    tok=Tokenizer.load(str(a.tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    summary={};details={}
    for job in plan(a.prefix):
        path=Path(job["checkpoint"])
        if not path.exists():p.error(f"missing checkpoint: {path}")
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        model.eval()
        with torch.no_grad():
            result=[evaluate_one(model,tok,row,probe,a.max_new_tokens)
                    for row in rows for probe in ("EXACT","PARAPHRASE")]
        details[job["variant"]]=result
        summary[job["variant"]]={probe:summarize([r for r in result if r["probe"]==probe])
                                 for probe in ("EXACT","PARAPHRASE")}
    out={"version":"v0.13.32","evaluation":"TRAINING_PAIRS_AND_NONINDEPENDENT_PARAPHRASES",
         "generation":"GREEDY","production_unchanged":True,"summary":summary,"details":details}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()
