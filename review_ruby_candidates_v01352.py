"""v0.13.52 prepare and adjudicate ruby-candidate human reviews.

All automatic decisions are forbidden. Review candidates refer to original
sentence indices and preserve exact contextual evidence. Output is write-once.
"""
import argparse,hashlib,json,random
from pathlib import Path
from classify_ruby_boundary_v01351 import CANDIDATE,inspect_match
from classify_inline_ruby_v01350 import DEFAULT_READINGS

DECISIONS={"ACCEPT","REJECT","UNSURE"}
def candidates(lines,readings=DEFAULT_READINGS,ambiguous_sample=100,seed=1352):
    ruby=[];ambiguous=[]
    for line_no,line in enumerate(lines,1):
        for m in CANDIDATE.finditer(line):
            detail=inspect_match(m,readings)
            item={"id":f"L{line_no}-C{m.start()}","line":line_no,
                  "start":m.start(),"end":m.end(),"surface":m.group(),
                  "context":line[max(0,m.start()-20):min(len(line),m.end()+20)],
                  "label":detail["label"],"kanji":detail["kanji"],
                  "reading":detail["reading"],"following":detail["following"],
                  "decision":None,"reviewer_note":""}
            (ruby if detail["label"]=="RUBY_CANDIDATE" else ambiguous).append(item)
    rng=random.Random(seed)
    sampled=rng.sample(ambiguous,min(ambiguous_sample,len(ambiguous)))
    return {"version":"v0.13.52","status":"HUMAN_REVIEW_PENDING",
            "candidate_total":len(ruby),"ambiguous_total":len(ambiguous),
            "ambiguous_sample_size":len(sampled),
            "review_items":ruby+sampled,"manual_review_complete":False,
            "notes":["Review decisions: ACCEPT, REJECT, UNSURE.",
                     "ACCEPT is a review judgment, not an automatic replacement.",
                     "Sampled ambiguous cases do not establish corpus-wide recall."]}

def validate(review):
    items=review.get("review_items")
    if not isinstance(items,list):raise ValueError("review_items missing")
    ids=set();counts={x:0 for x in DECISIONS};pending=0
    for item in items:
        identifier=item.get("id")
        if not identifier or identifier in ids:raise ValueError("duplicate or missing ID")
        ids.add(identifier)
        decision=item.get("decision")
        if decision is None:pending+=1
        elif decision not in DECISIONS:raise ValueError(f"invalid decision: {decision}")
        else:counts[decision]+=1
    return {"version":"v0.13.52","status":"REVIEW_COMPLETE" if pending==0 else "HUMAN_REVIEW_PENDING",
            "reviewed":len(items)-pending,"pending":pending,"counts":counts,
            "total_review_items":len(items),"manual_review_complete":pending==0,
            "automatic_replacements":0,"training_approved":False}

def write_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+"\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("results/aozora_789_curated_v01349.txt"))
    p.add_argument("--output",type=Path,default=Path("results/aozora_789_ruby_review_v01352.json"))
    p.add_argument("--ambiguous-sample",type=int,default=100)
    p.add_argument("--seed",type=int,default=1352)
    p.add_argument("--review",type=Path,help="existing manually edited review JSON; validate without changing it")
    p.add_argument("--report",type=Path,default=Path("results/aozora_789_ruby_review_summary_v01352.json"))
    a=p.parse_args()
    if a.review:
        payload=json.loads(a.review.read_text(encoding="utf-8-sig"))
        result=validate(payload)
        write_new(a.report,result)
        print(json.dumps(result,ensure_ascii=False))
        return
    if a.ambiguous_sample<0:p.error("negative sample")
    if not a.input.is_file():p.error(f"missing input: {a.input}")
    lines=a.input.read_text(encoding="utf-8-sig").splitlines()
    result=candidates(lines,ambiguous_sample=a.ambiguous_sample,seed=a.seed)
    result["source_sha256"]=hashlib.sha256(a.input.read_bytes()).hexdigest()
    write_new(a.output,result)
    print(json.dumps({k:result[k] for k in ("status","candidate_total","ambiguous_total",
                     "ambiguous_sample_size")},ensure_ascii=False))
    print("review:",a.output)
if __name__=="__main__":main()
