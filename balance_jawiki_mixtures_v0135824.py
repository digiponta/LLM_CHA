"""v0.13.58.24: balance existing staged W/WR/WRP mixtures by supervised tokens.

Uses only already-staged examples; never duplicates a sample beyond its
existing repeat_index. Does not train or approve. Common budget is the
minimum achievable across arms, so no arm is given extra learning exposure.
A rebalanced mixture cannot fix independent-holdout or corpus-quality gaps.
"""
import argparse,hashlib,json,random
from pathlib import Path

ARMS=("W","WR","WRP")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    with path.open(encoding="utf-8-sig") as f:
        return [json.loads(x) for x in f if x.strip()]

def measure(records):
    counts={}
    for r in records:
        count=sum(r["loss_mask"])
        if count!=r["supervised_tokens"] or len(r["loss_mask"])!=len(r["token_ids"])-1:
            raise ValueError("loss mask inconsistent")
        counts[r["domain"]]=counts.get(r["domain"],0)+count
    return counts

def balance(input_dir,output_dir,seed=135824,tolerance=512):
    if output_dir.exists():raise FileExistsError(output_dir)
    mpath=input_dir/"manifest.json"
    manifest=json.loads(mpath.read_text(encoding="utf-8-sig"))
    if manifest.get("status")!="EXPERIMENT_DATA_STAGED_NOT_APPROVED":
        raise ValueError("input status invalid")
    pools={}
    for arm in ARMS:
        path=input_dir/(arm+"_mixture.jsonl")
        if sha(path)!=manifest.get("output_sha256",{}).get(path.name):
            raise ValueError("SHA256 mismatch: "+path.name)
        rows=load(path)
        if any(r.get("approval")!="EXPERIMENT_CANDIDATE_ONLY" for r in rows):
            raise ValueError("unapproved row state")
        pools[arm]=rows
    totals={arm:sum(measure(rows).values()) for arm,rows in pools.items()}
    if min(totals.values())<=0:raise ValueError("empty experiment")
    target=min(totals.values())
    result={};summaries={}
    for arm,rows in pools.items():
        # Retain the source mix as closely as possible while matching a
        # common total. Prefer removing only excess Wikipedia tokens.
        rng=random.Random(seed+ARMS.index(arm))
        groups={}
        for row in rows:groups.setdefault(row["domain"],[]).append(row)
        for domain in groups:rng.shuffle(groups[domain])
        current=totals[arm]
        kept=rows[:]
        if current>target:
            # Removing wiki examples avoids further undersupplying Replay.
            wiki=groups.get("wiki",[])
            keep_ids={id(x) for x in kept}
            for row in wiki:
                if current<=target:break
                n=row["supervised_tokens"]
                if abs(current-n-target)<abs(current-target):
                    keep_ids.remove(id(row));current-=n
            kept=[row for row in kept if id(row) in keep_ids]
        rng.shuffle(kept)
        counts=measure(kept);realized=sum(counts.values())
        if abs(realized-target)>tolerance:
            raise ValueError(f"{arm}: cannot meet common budget within tolerance")
        original=manifest["experiments"][arm]
        summaries[arm]={
            "source_supervised_tokens":totals[arm],
            "realized_supervised_tokens":realized,
            "common_target_tokens":target,
            "deviation_tokens":realized-target,
            "supervised_tokens_by_domain":counts,
            "actual_token_ratios":{k:v/realized for k,v in counts.items()},
            "source_target_weights":original["target_weights"],
            "sample_count":len(kept),
            "max_reuse_observed":max((int(r.get("repeat_index",0))+1 for r in kept),default=0)}
        result[arm]=kept
    output_dir.mkdir(parents=True,exist_ok=False)
    hashes={}
    for arm,rows in result.items():
        p=output_dir/(arm+"_balanced.jsonl")
        with p.open("x",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
        hashes[p.name]=sha(p)
    report={
      "version":"v0.13.58.24","status":"BALANCED_STAGED_NOT_APPROVED",
      "input_manifest_sha256":sha(mpath),"common_target_tokens":target,
      "tolerance_tokens":tolerance,"seed":seed,"experiments":summaries,
      "file_sha256":hashes,"training_performed":False,
      "independent_holdout_verified":False,"human_review_approved":False,
      "production_promotion_allowed":False,
      "warnings":["Equalizing supervised-token totals does not equalize optimizer steps or unique data.",
                  "Repeated replay examples can overfit despite a reuse cap.",
                  "No final holdout or human review has been performed."]}
    (output_dir/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path,default=Path("results/jawiki_mixtures_v0135823"))
    p.add_argument("--output-dir",type=Path,default=Path("results/jawiki_balanced_v0135824"))
    p.add_argument("--seed",type=int,default=135824)
    p.add_argument("--tolerance",type=int,default=512)
    a=p.parse_args()
    if a.tolerance<0:p.error("tolerance must be >= 0")
    result=balance(a.input_dir,a.output_dir,a.seed,a.tolerance)
    print(json.dumps({"status":result["status"],"common_target_tokens":result["common_target_tokens"],
        "experiments":result["experiments"]},ensure_ascii=False))
    print("manifest:",a.output_dir/"manifest.json")
if __name__=="__main__":main()
