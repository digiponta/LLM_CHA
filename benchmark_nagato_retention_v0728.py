"""Evaluate Experimental LLM retention by cohort across two checkpoints."""
import argparse,json,hashlib
from pathlib import Path
from benchmark_longitudinal_v0726 import validate_probes,compare
from experimental_backend_v0711 import ExperimentalBackend

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def cohort_metrics(cases):
    result={}
    for cohort in ("old","new"):
        subset=[r for r in cases if r["cohort"]==cohort]
        result[cohort]={"count":len(subset),"exact":sum(r["exact"] for r in subset),
                        "rate":sum(r["exact"] for r in subset)/len(subset) if subset else None}
    return result

def evaluate(old,new,probes,base,tokenizer,output,*,factory=None):
    inputs=[Path(x).resolve() for x in (old,new,probes,base,tokenizer)]
    if Path(output).resolve() in inputs:raise ValueError("output overlaps inputs")
    rows=validate_probes(json.loads(Path(probes).read_text(encoding="utf-8")))
    if any(r.get("cohort") not in ("old","new") for r in rows):
        raise ValueError("probes require old/new cohort")
    hashes_before={str(p):digest(p) for p in inputs}
    if factory is None:
        def factory(path):
            return ExperimentalBackend(base,tokenizer,path)
    result=compare([old,new],rows,factory)
    first,last=[step["cases"] for step in result["checkpoints"]]
    old_first=[r for r in first if r["cohort"]=="old"]
    old_last=[r for r in last if r["cohort"]=="old"]
    retained_baseline=sum(r["exact"] for r in old_first)
    forgotten=sum(a["exact"] and not b["exact"] for a,b in zip(old_first,old_last))
    report={"version":"v0.7.28","checkpoints":result["checkpoints"],
        "cohorts":[cohort_metrics(first),cohort_metrics(last)],
        "old_initial_correct":retained_baseline,"old_lost":forgotten,
        "old_forgetting_rate":forgotten/retained_baseline if retained_baseline else None,
        "old_forgetting_measurable":retained_baseline>0,
        "protected_hashes_before":hashes_before,
        "protected_hashes_after":{str(p):digest(p) for p in inputs},
        "auto_promote":False,"factual_verification":"NOT_PERFORMED",
        "interpretation":"Exact reproduction of stored PENDING strings; not fact verification"}
    report["protected_unchanged"]=report["protected_hashes_before"]==report["protected_hashes_after"]
    if not report["protected_unchanged"]:raise RuntimeError("protected input changed")
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--old",required=True)
    p.add_argument("--new",required=True)
    p.add_argument("--probes",default="results/nagato_retention_v0728/probes.json")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/nagato_retention_v0728/report.json")
    a=p.parse_args()
    result=evaluate(a.old,a.new,a.probes,a.base,a.tokenizer,a.output)
    print(json.dumps({"version":result["version"],"old_initial_correct":result["old_initial_correct"],
      "old_lost":result["old_lost"],"old_forgetting_rate":result["old_forgetting_rate"],
      "cohorts":result["cohorts"],"protected_unchanged":result["protected_unchanged"]},
      ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()
