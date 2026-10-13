"""v0.4.28.13: export manual review template or summarize explicit human labels.

No semantic correctness is inferred from text similarity or Gate confidence.
"""
import argparse,csv,hashlib,json
from pathlib import Path

FIELDS=["id","turn","question","final_answer","gate_resolution","candidate_alignment",
        "literal_probe_identity","primary_relevant","probes_semantically_equivalent",
        "final_relevant","gate_appropriate","notes"]
BOOL_FIELDS=FIELDS[7:11]
def template(data):
    records=data.get("records")
    if not isinstance(records,list) or len(records)!=64:raise ValueError("requires 64 records")
    result=[];seen=set()
    for r in records:
        key=(r.get("id"),r.get("turn"))
        if key in seen:raise ValueError("duplicate id and turn")
        seen.add(key)
        if not isinstance(r.get("question"),str):raise ValueError("missing question")
        labels=r.get("manual_review",{})
        if not isinstance(labels,dict):raise ValueError("invalid review")
        row={f:r.get(f) for f in FIELDS[:7]}
        row.update({f:("" if labels.get(f) is None else str(labels.get(f))) for f in BOOL_FIELDS})
        row["notes"]=str(labels.get("notes",""))
        result.append(row)
    return result

def summarize(data, reviews):
    known={(r["id"],str(r["turn"])):r for r in template(data)}
    seen=set();evaluated=[];conflicts=[]
    for r in reviews:
        key=(r["id"],r["turn"])
        if key not in known or key in seen:raise ValueError("unknown/duplicate review "+str(key))
        seen.add(key)
        original=known[key]
        if r["question"]!=original["question"] or r["final_answer"]!=str(original["final_answer"]):
            raise ValueError("review/source mismatch "+str(key))
        labels={}
        for f in BOOL_FIELDS:
            value=r.get(f,"").strip().lower()
            if value not in ("","true","false"):raise ValueError("labels must be true/false/blank: "+f)
            labels[f]=None if not value else value=="true"
        label_count=sum(v is not None for v in labels.values())
        if label_count:
            evaluated.append({"id":key[0],"turn":key[1],"labels":labels})
            if labels["final_relevant"] is False and r["gate_resolution"]=="ACCEPT":
                conflicts.append({"id":key[0],"turn":key[1],"classification":"HUMAN_LABELED_ACCEPT_RELEVANCE_CONFLICT"})
    return {"version":"v0.4.28.13","development_only":True,
            "reviewed_turns":len(evaluated),"unreviewed_turns":64-len(evaluated),
            "labeled_accept_relevance_conflicts":len(conflicts),
            "conflicts":conflicts,"manual_evaluations":evaluated,
            "root_cause":"UNDETERMINED"}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--analysis",required=True)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--export-template")
    g.add_argument("--reviews")
    ap.add_argument("--output")
    args=ap.parse_args()
    try:
        src=Path(args.analysis)
        if not src.is_file() or src.is_symlink():raise ValueError("invalid analysis input")
        data=json.loads(src.read_text(encoding="utf-8"))
        if args.export_template:
            dst=Path(args.export_template)
            if dst.exists() or dst.is_symlink():raise ValueError("output already exists")
            dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open("x",newline="",encoding="utf-8-sig") as f:
                writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(template(data))
            print(json.dumps({"template_rows":64,"path":str(dst)},ensure_ascii=False))
        else:
            if not args.output:raise ValueError("--output required with --reviews")
            dst=Path(args.output)
            if dst.exists() or dst.is_symlink():raise ValueError("output already exists")
            with Path(args.reviews).open("r",encoding="utf-8-sig",newline="") as f:
                reader=csv.DictReader(f)
                if reader.fieldnames!=FIELDS:raise ValueError("invalid CSV headers")
                rows=list(reader)
            summary=summarize(data,rows)
            summary["analysis_sha256"]=hashlib.sha256(src.read_bytes()).hexdigest()
            summary["review_sha256"]=hashlib.sha256(Path(args.reviews).read_bytes()).hexdigest()
            dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open("x",encoding="utf-8") as f:json.dump(summary,f,ensure_ascii=False,indent=2);f.write("\n")
            print(json.dumps({k:summary[k] for k in ("reviewed_turns","unreviewed_turns","labeled_accept_relevance_conflicts")}))
    except (OSError,ValueError,json.JSONDecodeError) as e:ap.exit(1,f"validation failed: {e}\n")
if __name__=="__main__":main()
