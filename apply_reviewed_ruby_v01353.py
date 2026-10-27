"""Apply manually reviewed ruby removals at exact source positions (v0.13.53).

Requires completed review and source SHA256 match; never uses global replace.
No training approval. Existing outputs are never overwritten.
"""
import argparse,hashlib,json
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def propose(item,line,override=None):
    start,end=item["start"],item["end"]
    if not (0<=start<end<=len(line)) or line[start:end]!=item["surface"]:
        raise ValueError(f"source location mismatch: {item['id']}")
    kanji,reading=item.get("kanji"),item.get("reading")
    if override is not None:
        if reading is not None:
            raise ValueError(f"unexpected override for classified reading: {item['id']}")
        kanji,reading=override["kanji"],override["reading"]
    if not (isinstance(kanji,str) and kanji and isinstance(reading,str) and reading):
        raise ValueError(f"ACCEPT lacks explicit dictionary reading: {item['id']}")
    surface=item["surface"]
    marker=kanji+reading
    # Kanji may be preceded by other Kanji inside regex token.
    offset=surface.find(marker)
    if offset<0 or surface.count(marker)!=1:
        raise ValueError(f"cannot unambiguously identify reading: {item['id']}")
    rs=start+offset+len(kanji);re=rs+len(reading)
    if line[rs:re]!=reading:raise ValueError(f"reading mismatch: {item['id']}")
    return {"id":item["id"],"line":item["line"],"start":rs,"end":re,
            "removed":reading,"surface":surface,"decision":"ACCEPT"}

def apply_review(lines,review,overrides=None):
    overrides=overrides or {}
    if review.get("version")!="v0.13.52" or review.get("manual_review_complete") is not True:
        raise ValueError("review must be finalized v0.13.52")
    items=review.get("review_items",[])
    if not items or any(it.get("decision") not in ("ACCEPT","REJECT","UNSURE") for it in items):
        raise ValueError("all decisions must be explicit")
    changes=[];ids=set()
    for it in items:
        if it["id"] in ids:raise ValueError("duplicate review ID")
        ids.add(it["id"])
        if it["decision"]!="ACCEPT":continue
        ln=it["line"]
        if not isinstance(ln,int) or not 1<=ln<=len(lines):raise ValueError("invalid line")
        changes.append(propose(it,lines[ln-1],overrides.get(it["id"])))
    byline={}
    for change in changes:byline.setdefault(change["line"],[]).append(change)
    out=list(lines)
    for ln,edits in byline.items():
        # Work backwards so original indices remain valid.
        edits.sort(key=lambda e:e["start"],reverse=True)
        previous=len(out[ln-1])+1
        for e in edits:
            if e["end"]>previous:raise ValueError(f"overlapping edits: line {ln}")
            previous=e["start"]
            source=out[ln-1]
            if source[e["start"]:e["end"]]!=e["removed"]:raise ValueError("edit mismatch")
            out[ln-1]=source[:e["start"]]+source[e["end"]:]
    return out,changes

def run(source,review_path,output,report,readings_path=None):
    if output.exists() or report.exists():raise FileExistsError("refusing to overwrite")
    review=json.loads(review_path.read_text(encoding="utf-8-sig"))
    if sha(source)!=review.get("source_sha256"):raise ValueError("source SHA256 mismatch")
    original=source.read_text(encoding="utf-8-sig")
    lines=original.splitlines()
    overrides={}
    if readings_path:
        readings_doc=json.loads(readings_path.read_text(encoding="utf-8-sig"))
        if readings_doc.get("version")!="v0.13.53" or not isinstance(readings_doc.get("readings"),dict):
            raise ValueError("invalid approved readings document")
        overrides=readings_doc["readings"]
    revised,changes=apply_review(lines,review,overrides)
    counts={k:sum(i.get("decision")==k for i in review["review_items"]) for k in ("ACCEPT","REJECT","UNSURE")}
    audit={"version":"v0.13.53","status":"APPLIED_REVIEWED_ONLY",
           "source_sha256":sha(source),"review_sha256":sha(review_path),
           "source_lines":len(lines),"result_lines":len(revised),
           "accepted":counts["ACCEPT"],"rejected":counts["REJECT"],
           "unsure":counts["UNSURE"],"applied":len(changes),
           "edits":changes,"training_approved":False,
           "limitations":["Unambiguous position-matched edits only; sampled review does not cover the entire corpus.",
                          "This is not proof of independent evaluation."]}
    # Preserve newline style in text format: normalized corpus has LF lines.
    output.parent.mkdir(parents=True,exist_ok=True)
    report.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8",newline="\n") as f:f.write("\n".join(revised)+"\n")
    with report.open("x",encoding="utf-8") as f:json.dump(audit,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:audit[k] for k in ("status","applied","rejected","unsure","training_approved")},ensure_ascii=False))
    print("report:",report)
    return audit

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--approved-readings",type=Path)
    p.add_argument("--review",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    run(a.input,a.review,a.output,a.report,a.approved_readings)
if __name__=="__main__":main()
