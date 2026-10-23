"""Build fixed old/new training probes for Nagato Experimental checkpoint audit."""
import argparse
import json
from pathlib import Path
import torch
from dual_semantic_memory_v071 import DualMemory

def prepare(old_path,new_path,approved_path,candidates_path,output):
    old=torch.load(old_path,map_location="cpu",weights_only=True)
    new=torch.load(new_path,map_location="cpu",weights_only=True)
    for saved in (old,new):
        if saved.get("route")!="experimental" or saved.get("approved") is not False:
            raise ValueError("checkpoint must be Experimental only")
    old_ids=set(old["candidate_ids"])
    new_ids=set(new["candidate_ids"])
    if not old_ids<=new_ids:raise ValueError("old knowledge IDs missing in new checkpoint")
    memory=DualMemory(approved_path,candidates_path)
    pending={r["id"]:r for r in memory.candidates() if r["status"]=="PENDING"}
    missing=new_ids-pending.keys()
    if missing:raise ValueError("new checkpoint IDs missing from PENDING memory")
    rows=[]
    for candidate_id in sorted(new_ids):
        record=pending[candidate_id]
        rows.append({"knowledge_id":candidate_id,"split":"train",
                     "question":record["question"],"reference":record["answer"],
                     "cohort":"old" if candidate_id in old_ids else "new",
                     "source_id":record["source_id"]})
    out=Path(output)
    protected={Path(p).resolve() for p in
               (old_path,new_path,approved_path,candidates_path)}
    if out.resolve() in protected:raise ValueError("output overlaps protected input")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"old_candidates":len(old_ids),"new_candidates":len(new_ids-old_ids),
            "total_probes":len(rows),"output":str(out),"memory_changed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--old",required=True)
    p.add_argument("--new",required=True)
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--output",default="results/nagato_retention_v0728/probes.json")
    args=p.parse_args()
    print(json.dumps(prepare(args.old,args.new,args.approved,args.candidates,args.output),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
