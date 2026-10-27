"""v0.13.49 conservative inline-ruby curation.

Only EXACT operator-reviewed literal pairs are replaced. No generic kanji/kana
heuristic replacement, no source mutation, no implicit training approval.
Rules example:
{"rules":[{"surface":"吾輩わがはい","replacement":"吾輩","reviewed":true,
            "reason":"reading appended in extracted text"}]}
"""
import argparse,hashlib,json
from pathlib import Path

def validate_rules(document):
    rules=document.get("rules")
    if not isinstance(rules,list):raise ValueError("rules array required")
    seen=set();out=[]
    for r in rules:
        if not isinstance(r,dict) or r.get("reviewed") is not True or not r.get("reason"):
            raise ValueError("each rule requires manual reviewed=true and reason")
        s=r.get("surface");t=r.get("replacement")
        if not isinstance(s,str) or not isinstance(t,str) or not s or not t or s==t:
            raise ValueError("invalid replacement")
        if "\n" in s or "\n" in t:raise ValueError("rules must be single line")
        if s in seen:raise ValueError("duplicate surface")
        seen.add(s);out.append((s,t,r["reason"]))
    return sorted(out,key=lambda x:len(x[0]),reverse=True)

def apply(lines,rules):
    rows=[];changes=[]
    for i,line in enumerate(lines,1):
        new=line
        for old,repl,reason in rules:
            count=new.count(old)
            if count:
                new=new.replace(old,repl)
                changes.append({"line":i,"surface":old,"replacement":repl,
                                "occurrences":count,"reason":reason})
        rows.append(new)
    return rows,changes

def curate(source,rules_file,output,report):
    if output.exists() or report.exists():raise FileExistsError("refusing overwrite")
    document=json.loads(rules_file.read_text(encoding="utf-8-sig"))
    rules=validate_rules(document)
    raw=source.read_text(encoding="utf-8-sig")
    lines=raw.splitlines()
    revised,changes=apply(lines,rules)
    a={"version":"v0.13.49","status":"CURATED_REVIEW_REQUIRED",
       "input":str(source),"rules_file":str(rules_file),
       "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
       "rules_sha256":hashlib.sha256(rules_file.read_bytes()).hexdigest(),
       "input_lines":len(lines),"output_lines":len(revised),
       "changed_lines":len({x["line"] for x in changes}),
       "replacements":sum(x["occurrences"] for x in changes),
       "changes":changes,"training_approved":False,
       "limitations":["Exact string rules can match inside longer words; manually inspect the diff.",
                      "Historical model exposure is not resolved by text curation.",
                      "This is not automatic ruby recognition."]}
    output.parent.mkdir(parents=True,exist_ok=True)
    report.parent.mkdir(parents=True,exist_ok=True)
    output.write_text("\n".join(revised)+"\n",encoding="utf-8")
    report.write_text(json.dumps(a,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return a

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--rules",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    for f in (a.input,a.rules):
        if not f.is_file():p.error(f"missing input: {f}")
    result=curate(a.input,a.rules,a.output,a.report)
    print(json.dumps({k:result[k] for k in
        ("status","input_lines","changed_lines","replacements","training_approved")},ensure_ascii=False))
    print("report:",a.report)
if __name__=="__main__":main()
