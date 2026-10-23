"""v0.7.26 read-only longitudinal Experimental knowledge retention benchmark."""
import argparse,json
from pathlib import Path

def validate_probes(rows):
    if not isinstance(rows,list) or not rows:raise ValueError("nonempty probe list required")
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or any(not isinstance(row.get(k),str) or not row[k].strip()
                for k in ("question","reference","knowledge_id","split")):
            raise ValueError("invalid probe")
        if row["split"] not in ("train","paraphrase"):
            raise ValueError("split must be train or paraphrase")
        k=(row["knowledge_id"],row["question"].strip())
        if k in seen:raise ValueError("duplicate probe")
        seen.add(k)
    return rows

def metrics(rows):
    by={}
    for r in rows:
        key=r["split"]
        by.setdefault(key,[]).append(r)
    return {k:{"count":len(v),"exact":sum(x["exact"] for x in v),
               "accuracy":sum(x["exact"] for x in v)/len(v)} for k,v in by.items()}

def compare(checkpoint_paths,probes,backend_factory):
    validate_probes(probes)
    if not checkpoint_paths:raise ValueError("checkpoint required")
    steps=[]
    for path in checkpoint_paths:
        backend=backend_factory(path)
        rows=[]
        for p in probes:
            answer=backend(p["question"])
            rows.append({**p,"generated":answer,"exact":answer.strip()==p["reference"].strip()})
        steps.append({"checkpoint":str(path),"metrics":metrics(rows),"cases":rows})
    first={ (x["knowledge_id"],x["question"]):x for x in steps[0]["cases"]}
    last={ (x["knowledge_id"],x["question"]):x for x in steps[-1]["cases"]}
    previously_correct=sum(x["exact"] for x in first.values())
    lost=sum(x["exact"] and not last[k]["exact"] for k,x in first.items())
    return {"version":"v0.7.26","checkpoints":steps,"initially_correct":previously_correct,
            "lost_correct":lost,
            "forgetting_rate":lost/previously_correct if previously_correct else None,
            "forgetting_measurable":previously_correct>0 and len(steps)>1,
            "auto_promote":False,"factual_verification":"NOT_PERFORMED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoints",nargs="+",required=True)
    p.add_argument("--probes",required=True)
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/experimental_longitudinal_v0726/report.json")
    a=p.parse_args()
    from experimental_backend_v0711 import ExperimentalBackend
    from experimental_reload_v0723 import validated_backend
    from dual_semantic_memory_v071 import DualMemory
    import torch
    rows=validate_probes(json.loads(Path(a.probes).read_text(encoding="utf-8")))
    # Longitudinal checkpoints can have different candidate ID snapshots.
    # They must remain experimental-only and match the same frozen base.
    def factory(path):
        saved=torch.load(path,map_location="cpu",weights_only=True)
        if saved.get("route")!="experimental" or saved.get("approved") is not False:
            raise ValueError("not experimental-only checkpoint")
        if not saved.get("candidate_ids"):raise ValueError("missing candidate identities")
        backend=ExperimentalBackend(a.base,a.tokenizer,path)
        return backend
    result=compare(a.checkpoints,rows,factory)
    out=Path(a.output)
    protected=[Path(x).resolve() for x in
               [a.base,a.tokenizer,a.probes,*a.checkpoints]]
    if out.resolve() in protected:raise ValueError("output overlaps inputs")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"version":result["version"],"checkpoints":len(result["checkpoints"]),
          "initially_correct":result["initially_correct"],"lost_correct":result["lost_correct"],
          "forgetting_rate":result["forgetting_rate"],
          "forgetting_measurable":result["forgetting_measurable"]},ensure_ascii=False,indent=2))
    print("report:",out)
if __name__=="__main__":main()
