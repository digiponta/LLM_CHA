"""v0.2.17 blind response-quality comparison using v0.2.16 EOS traces.

Generate a blinded rating CSV; never infer fluency from answer length alone.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,random
from pathlib import Path
from collections import defaultdict

DIMENSIONS=("naturalness","topic_relevance","substance","coherence")
def blind_records(report,model_filter=None):
    items=[]
    for model,methods in report["models"].items():
        if model_filter and not any(v in model for v in model_filter):continue
        for method,entry in methods.items():
            for i,r in enumerate(entry["records"]):
                items.append({"model":model,"method":method,"prompt_id":i,
                 "prompt":r["prompt"],"reference":r["reference"],"generated":r["generated"],
                 "tokens":r["tokens"],"eos":r["terminated_by_eos"]})
    return items
def build(input_path,output_dir,seed=42,model_filter=None):
    data=json.loads(Path(input_path).read_text(encoding="utf-8"))
    items=blind_records(data,model_filter)
    if not items:raise ValueError("No matching output records")
    rng=random.Random(seed)
    rng.shuffle(items)
    destination=Path(output_dir);destination.mkdir(parents=True,exist_ok=True)
    # Rating sheet has neither model nor decoding label. Identifier maps privately.
    with (destination/"blind_ratings.csv").open("w",encoding="utf-8-sig",newline="") as f:
        wr=csv.writer(f)
        wr.writerow(["id","prompt","generated",*(d+"_1_to_5" for d in DIMENSIONS),"unintelligible_0_or_1"])
        for i,r in enumerate(items):wr.writerow([f"R{i+1:04d}",r["prompt"],r["generated"],"","","","",""])
    with (destination/"blind_key.json").open("w",encoding="utf-8") as f:
        json.dump({f"R{i+1:04d}":r for i,r in enumerate(items)},f,ensure_ascii=False,indent=2)
    return len(items)
def score(ratings_path,key_path):
    key=json.loads(Path(key_path).read_text(encoding="utf-8"))
    accum=defaultdict(list)
    with Path(ratings_path).open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            ident=row["id"]
            if ident not in key:raise ValueError("Unknown response ID "+ident)
            raw=[row[d+"_1_to_5"].strip() for d in DIMENSIONS]
            flag=row["unintelligible_0_or_1"].strip()
            if not any(raw) and not flag:continue
            if not all(raw) or flag not in ("0","1"):raise ValueError("Incomplete scoring for "+ident)
            vals=[int(x) for x in raw]
            if any(not 1<=v<=5 for v in vals):raise ValueError("Out of range score at "+ident)
            r=key[ident];accum[(r["model"],r["method"])].append(dict(zip(DIMENSIONS,vals),unintelligible=int(flag)))
    results={}
    for (model,method),entries in sorted(accum.items()):
        if len(entries)<10:continue
        means={d:round(sum(r[d] for r in entries)/len(entries),3) for d in DIMENSIONS}
        # Predeclared quality target; no automatic adoption.
        means["quality_score"]=round(.3*means["naturalness"]+.35*means["topic_relevance"]+
                                    .2*means["substance"]+.15*means["coherence"],3)
        means["unintelligible_fraction"]=round(sum(r["unintelligible"] for r in entries)/len(entries),4)
        means["rated"]=len(entries)
        results.setdefault(model,{})[method]=means
    return results
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="results/eos_decoding_v0216.json")
    p.add_argument("--output-dir",default="results/decoding_quality_v0217")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--score",action="store_true")
    a=p.parse_args()
    path=Path(a.output_dir)
    if a.score:
        result=score(path/"blind_ratings.csv",path/"blind_key.json")
        (path/"scores.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print("Blind responses:",build(a.source,path,a.seed))
        print("Rate blind_ratings.csv, then use --score. Keep blind_key.json private until ratings are finalized.")
if __name__=="__main__":main()
