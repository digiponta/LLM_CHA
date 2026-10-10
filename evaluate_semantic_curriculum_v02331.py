"""Three-way held-out raw/short free generation, same decoding conditions."""
import argparse,json
from pathlib import Path
from dialogue_guided_generation_v02322 import CheckpointGenerator
from evaluate_semantic_transfer_v02327 import PROBES,LEGACY,prompt_for

def evaluate(models,probes,max_new_tokens=80):
    out=[]
    for item in probes:
        kinds=["raw"] if item["kind"]=="legacy" else ["raw","short"]
        rows={}
        for kind in kinds:
            prompt=f"人: {item['user']}\nAI: " if kind=="raw" else prompt_for(item)
            rows[kind]={name:obj.generate(prompt,max_new_tokens=max_new_tokens,temperature=0.0)
                         for name,obj in models.items()}
        out.append({"kind":item["kind"],"user":item["user"],"results":rows,
                    "manual_review":None})
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--baseline",default="model/model-llm-cha-curriculum-baseline-v02331.pt")
    p.add_argument("--curriculum",default="model/model-llm-cha-curriculum-staged-v02331.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--out",default="results/semantic_curriculum_eval_v02331.json")
    args=p.parse_args()
    models={k:CheckpointGenerator(v,args.tokenizer,args.device) for k,v in
            (("base",args.base),("baseline",args.baseline),("curriculum",args.curriculum))}
    rows=evaluate(models,PROBES+LEGACY,args.max_new_tokens)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"results":rows,"promotion_eligible":False,
         "note":"Exploratory probes repeated from earlier experiments; independent held-out test required."},
         ensure_ascii=False,indent=2),encoding="utf-8")
    for row in rows:
        print(f"[{row['kind']}] {row['user']}")
        for mode,outputs in row["results"].items():
            for k,v in outputs.items():print(f" {mode:5s} {k:10s}: {v['text']!r}")
    print("Saved:",dest)
if __name__=="__main__":main()
