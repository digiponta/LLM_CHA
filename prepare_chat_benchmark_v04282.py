"""Parse fixed chat benchmark into evaluation-only case manifest (v0.4.28.2).

Does NOT run chat.py, train, capture or write memory.
"""
import argparse
import json
import re
from pathlib import Path

HEADING=re.compile(r"^## ([A-G]):.*?/(SINGLE|MULTI)")
CASE=re.compile(r"^# ([A-EG][0-9]{2})$")
MULTI=re.compile(r"^# (F[1-4]) (START|END)(?:\\b|$)")
EXPECTED={"A":12,"B":12,"C":8,"D":8,"E":8,"F":12,"G":4}

def parse(text):
    category=None; mode=None; case=None; active=None; groups=[]; seen=set(); counts={k:0 for k in EXPECTED}
    for line_no,raw in enumerate(text.splitlines(),1):
        line=raw.strip()
        if not line:continue
        heading=HEADING.match(line)
        if heading:
            if active is not None:raise ValueError(f"line {line_no}: unfinished multi-turn")
            category,mode=heading.groups();case=None
            continue
        match=MULTI.match(line)
        if match:
            ident,action=match.groups()
            if category!="F" or mode!="MULTI":raise ValueError(f"line {line_no}: misplaced multi marker")
            if action=="START":
                if active is not None or ident in seen:raise ValueError(f"line {line_no}: duplicate/overlap")
                active={"id":ident,"category":"F","mode":"MULTI","prompts":[]}
            else:
                if active is None or active["id"]!=ident or not active["prompts"]:
                    raise ValueError(f"line {line_no}: unmatched END")
                groups.append(active);seen.add(ident);active=None
            continue
        match=CASE.fullmatch(line)
        if match:
            ident=match.group(1)
            if category!=ident[0] or mode!="SINGLE" or case is not None or ident in seen:
                raise ValueError(f"line {line_no}: invalid case ID")
            case=ident
            continue
        if line.startswith("#"):continue
        if category is None:raise ValueError(f"line {line_no}: prompt outside category")
        if mode=="SINGLE":
            if case is None:raise ValueError(f"line {line_no}: missing case ID")
            groups.append({"id":case,"category":category,"mode":"SINGLE","prompts":[line]})
            seen.add(case);case=None
        elif mode=="MULTI":
            if active is None:raise ValueError(f"line {line_no}: prompt outside multi-turn group")
            active["prompts"].append(line)
        else:raise ValueError(f"line {line_no}: bad mode")
        counts[category]+=1
    if active is not None or case is not None:raise ValueError("unfinished group")
    if counts!=EXPECTED or len(groups)!=56:
        raise ValueError(f"benchmark shape mismatch: counts={counts}, groups={len(groups)}")
    return {"version":"v0.4.28.2","purpose":"DEVELOPMENT_EVALUATION_ONLY",
            "independent_holdout":False,"training_enabled":False,
            "chat_execution_enabled":False,"count":sum(counts.values()),
            "groups":groups,"category_counts":counts}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        source=Path(a.input);out=Path(a.output)
        if not source.is_file() or source.is_symlink():raise ValueError("missing or symlink input")
        result=parse(source.read_text(encoding="utf-8-sig"))
        if out.exists() or out.is_symlink():raise ValueError("output already exists")
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({"count":result["count"],"groups":len(result["groups"]),
                          "category_counts":result["category_counts"]},ensure_ascii=False))
    except (OSError,ValueError) as e:
        p.exit(1,"benchmark preparation failed: "+str(e)+"\n")
if __name__=="__main__":main()
