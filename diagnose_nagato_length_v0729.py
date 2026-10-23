"""v0.7.29 diagnose long Nagato Candidate generation without training."""
import argparse,json
from pathlib import Path

def common_prefix(a,b):
    count=0
    for x,y in zip(a,b):
        if x!=y:break
        count+=1
    return count

def analyze_records(rows,encode,generate,max_new_tokens=32,context_length=512):
    if max_new_tokens<1:raise ValueError("invalid generation limit")
    cases=[]
    for r in rows:
        target=encode(r["answer"])
        prompt=encode("人: "+r["question"]+"\nAI: ")
        output=generate(r["question"])
        generated=encode(output)
        prefix=common_prefix(target,generated)
        cases.append({"candidate_id":r["id"],"source_id":r["source_id"],
          "answer_tokens":len(target),"prompt_tokens":len(prompt),
          "generation_budget":max_new_tokens,
          "exceeds_generation_budget":len(target)>max_new_tokens,
          "exceeds_context_window":len(prompt)+len(target)>context_length,
          "generated_tokens":len(generated),"prefix_tokens":prefix,
          "prefix_fraction":prefix/len(target) if target else None,
          "exact_match":output.strip()==r["answer"].strip(),
          "generated_preview":output[:180],"answer_preview":r["answer"][:180]})
    return {"version":"v0.7.29","count":len(cases),
      "too_long_for_budget":sum(x["exceeds_generation_budget"] for x in cases),
      "too_long_for_context":sum(x["exceeds_context_window"] for x in cases),
      "exact":sum(x["exact_match"] for x in cases),
      "cases":cases,"factual_verification":"NOT_PERFORMED","auto_promote":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--adapter",required=True)
    p.add_argument("--max-new-tokens",type=int,default=32)
    p.add_argument("--output",default="results/nagato_diagnostic_v0729/report.json")
    a=p.parse_args()
    from dual_semantic_memory_v071 import DualMemory
    from tokenizer_bpe import Tokenizer
    from experimental_backend_v0711 import ExperimentalBackend
    memory=DualMemory(a.approved,a.candidates)
    rows=[r for r in memory.candidates() if r["status"]=="PENDING" and
          r["source_id"].startswith("data-nagato.txt:")]
    if not rows:raise ValueError("no PENDING Nagato records")
    tokenizer=Tokenizer.load(a.tokenizer)
    backend=ExperimentalBackend(a.base,a.tokenizer,a.adapter)
    # Existing inference backend uses a fixed 32-token generation budget.
    if a.max_new_tokens!=32:
        raise ValueError("current ExperimentalBackend generates 32 tokens; use 32")
    result=analyze_records(rows,lambda text:tokenizer.encode(text),
                           backend,max_new_tokens=32,context_length=512)
    output=Path(a.output)
    protected={Path(x).resolve() for x in
        (a.approved,a.candidates,a.base,a.tokenizer,a.adapter)}
    if output.resolve() in protected:raise ValueError("output overlaps protected inputs")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in
        ("version","count","too_long_for_budget","too_long_for_context","exact")},
        ensure_ascii=False,indent=2))
    print("report:",output)
if __name__=="__main__":main()
