"""v0.5.55 checkpoint comparison: independent prompts vs history effects.

All checkpoints share a tokenizer, evaluation inputs, deterministic decoding
and identical prompt construction. Metrics are diagnostic only, not human quality.
"""
import argparse,json
from pathlib import Path
from diagnose_persona_generation_v0554 import diagnose

def prompts(turns, mode, outputs=None):
    history=[]
    result=[]
    for i,user in enumerate(turns):
        if mode=="single":
            h=[]
        elif mode=="gold":
            h=[(x["user"],x["reference_answer"]) for x in turns[:i]]
        elif mode=="self":
            h=history
        else:raise ValueError("unknown mode")
        prompt="".join("人: "+u+"\nAI: "+a+"\n" for u,a in h[-3:])+"人: "+user["user"]+"\nAI:"
        result.append(prompt)
        if mode=="self":
            if outputs is None:raise ValueError("self requires generated outputs")
            # Current turn has not been generated yet. Only previous turns
            # can enter the autoregressive conversational history.
            if i < len(outputs):
                history.append((user["user"],outputs[i]))
    return result

def generate_mode(turns,mode,generate):
    generated=[]
    for i,row in enumerate(turns):
        prompt=prompts(turns[:i+1],mode,generated if mode=="self" else None)[-1]
        output=generate(prompt)
        if not isinstance(output,str):raise TypeError("generation must return text")
        generated.append(output)
    return [{"turn":i+1,"user":t["user"],"reply":a,"diagnostics":diagnose(a,t["user"])}
            for i,(t,a) in enumerate(zip(turns,generated))]

def compare(dataset,load):
    report=[]
    for m in dataset["models"]:
        generator,meta=load(m["path"])
        cases=[]
        for case in dataset["scenarios"]:
            for mode in ("single","gold","self"):
                cases.append({"id":case["id"],"mode":mode,
                              "rows":generate_mode(case["turns"],mode,generator)})
        report.append({"name":m["name"],"checkpoint":meta,"cases":cases})
    return {"version":"v0.5.55","protocol":"CHECKPOINT_AND_HISTORY_ABLATION",
            "decoding":"temperature=0,max_new_tokens=64,top_k=20,repeat_penalty=1.05",
            "human_persona_quality":None,"topic_relevance_accuracy":None,
            "claim_of_forgetting":False,"results":report}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/checkpoint_comparison_v0555.json")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",default="auto")
    p.add_argument("--output",default="results/checkpoint_comparison_v0555.json")
    args=p.parse_args()
    from evaluate_persona_ablation_v0552 import load_generator
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    def loader(path):return load_generator(path,args.tokenizer,args.device,64)
    result=compare(data,loader)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"version":result["version"],"checkpoints":[r["name"] for r in result["results"]],
     "comparisons":sum(len(r["cases"]) for r in result["results"]),"output":str(path)},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
