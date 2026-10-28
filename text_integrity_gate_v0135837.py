"""v0.13.58.37: non-destructive text-integrity gate.

Do not delete raw experiment evidence. Reject U+FFFD and illegal control
characters before SFT; quarantine malformed model outputs before any future
training-data promotion. Invalid UTF-8 is rejected (never replaced).
"""
import argparse,json,hashlib,unicodedata
from pathlib import Path

def defects(text):
    if not isinstance(text,str):return ["NON_STRING"]
    found=[]
    if "\ufffd" in text:found.append("REPLACEMENT_CHARACTER_U_FFFD")
    if any((ord(c)<32 and c not in "\t\n\r") or ord(c)==127 for c in text):
        found.append("ILLEGAL_CONTROL_CHARACTER")
    return found

def validate_training_records(rows):
    good=[];bad=[]
    for pos,row in enumerate(rows):
        issues=[]
        for field in ("user","assistant"):
            issues.extend(field+":"+d for d in defects(row.get(field)))
        entry={"index":pos,"id":row.get("id"),"issues":issues}
        if issues:bad.append(entry)
        else:good.append(row)
    return good,bad

def read_jsonl_strict(path):
    rows=[]
    for index,line in enumerate(path.read_text(encoding="utf-8-sig",errors="strict").splitlines(),1):
        if line.strip():
            obj=json.loads(line)
            if not isinstance(obj,dict):raise ValueError(f"line {index}: object required")
            rows.append(obj)
    return rows

def audit(source,output,generated_report=None):
    if output.exists():raise FileExistsError(output)
    rows=read_jsonl_strict(source)
    good,bad=validate_training_records(rows)
    quarantine=[]
    if generated_report:
        data=json.loads(generated_report.read_text(encoding="utf-8-sig",errors="strict"))
        for e in data.get("events",[]):
            issue=defects(e.get("answer",""))
            if issue:quarantine.append({"id":e.get("id"),"round":e.get("round"),"issues":issue})
    report={"version":"v0.13.58.37","status":"TEXT_INTEGRITY_AUDIT_COMPLETE",
       "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
       "record_count":len(rows),"safe_records":len(good),
       "excluded_training_records":bad,
       "generation_quarantine":quarantine,
       "original_evidence_modified":False,"training_performed":False,
       "production_promotion_allowed":False}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/literature_fact_corrections_v0135836.jsonl"))
    p.add_argument("--generated-report",type=Path,default=Path("results/literature_facts_v0135836/report.json"))
    p.add_argument("--output",type=Path,default=Path("results/literature_text_integrity_v0135837.json"))
    a=p.parse_args();r=audit(a.source,a.output,a.generated_report)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
