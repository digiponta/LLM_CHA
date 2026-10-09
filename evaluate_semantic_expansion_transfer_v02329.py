"""v0.2.32.9: three-checkpoint independent free-generation comparisons.

Run the same frozen evaluation prompts with no purpose metadata (raw) and
with short Topic/Purpose conditions. No promotion and no invented quality scores.
"""
import argparse,json,datetime
from pathlib import Path
from dialogue_guided_generation_v02322 import CheckpointGenerator
from semantic_memory_expansion_v02328 import load_rows
from evaluate_semantic_transfer_v02327 import PROBES,LEGACY,prompt_for

def evaluation_cases(expansion):
    rows=load_rows(expansion)
    trained={r["prompt"] for r in rows if r["review_status"]=="APPROVED"}
    originals=[r for r in rows if r["variant_type"]=="original" and r["review_status"]=="APPROVED"]
    cases=[]
    for r in originals:
        # Keep teacher cases separate from independent/generalization results.
        c=r["canonical"];user=r["prompt"].split("\n人: ",1)[1].rsplit("\nAI: ",1)[0]
        cases.append({"group":"teacher","user":user,"topic":c["topic"],
                      "purpose":",".join(c["purposes"]),"expected_answer":r["answer"]})
    for p in PROBES:
        cases.append({"group":p["kind"],**{k:v for k,v in p.items() if k!="kind"}})
    for p in LEGACY:
        cases.append({"group":"legacy","user":p["user"],"expected":p.get("expected",[])})
    for case in cases:
        if case["group"] not in ("teacher","legacy"):
            labelled=prompt_for({"kind":"unseen",**case})
            if labelled in trained:raise ValueError("Holdout contamination: "+case["user"])
    if len({(x["group"],x["user"]) for x in cases})!=len(cases):
        raise ValueError("Duplicate evaluation cases")
    return cases

def prompts(case):
    raw=f"人: {case['user']}\nAI: "
    if case["group"]=="legacy":return {"raw":raw}
    labelled=prompt_for({"kind":"unseen",**case})
    return {"raw":raw,"short":labelled}

def compare(models,cases,max_new_tokens=80):
    out=[]
    for case in cases:
        outputs={}
        for mode,prompt in prompts(case).items():
            outputs[mode]={}
            for name,model in models.items():
                outputs[mode][name]=model.generate(prompt,max_new_tokens=max_new_tokens,temperature=0.0)
        out.append({**case,"outputs":outputs,"review":{"purpose_fidelity":None,
                    "fluency":None,"correctness":None,"retention":None}})
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--expansion",default="data/semantic_expansion_v02328.jsonl")
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--original",default="model/model-llm-cha-memory-original-v02328.pt")
    p.add_argument("--expanded",default="model/model-llm-cha-memory-expanded-v02328.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--out",default="results/semantic_expansion_transfer_v02329.json")
    a=p.parse_args()
    cases=evaluation_cases(a.expansion)
    models={name:CheckpointGenerator(path,a.tokenizer,a.device) for name,path in
            (("base",a.base),("original",a.original),("expanded",a.expanded))}
    result=compare(models,cases,a.max_new_tokens)
    report={"experiment":"v0.2.32.9","date":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "model_paths":{"base":a.base,"original":a.original,"expanded":a.expanded},
            "promotion_eligible":False,
            "caution":"Narrow, reused exploratory probes; raw tests DSS-free response generation, not DSS-free purpose understanding in an interactive session.",
            "results":result}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for r in result:
        print(f"[{r['group']}] {r['user']}")
        for mode,results in r["outputs"].items():
            print(" mode:",mode)
            for name,value in results.items():print("  ",name,repr(value["text"]))
    print("Saved",dest,"Promotion: BLOCKED pending independently rated generation evidence.")
if __name__=="__main__":main()
