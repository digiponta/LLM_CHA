"""v0.4.28.20: export review worksheet, never auto-assign human labels."""
import argparse,csv,json
from pathlib import Path
from review_semantic_relevance_v042813 import FIELDS,template

def worksheet(validation):
    base=template(validation)
    order=lambda row:(0 if row["id"] in {"A04","A05","C05","C07"} and row["turn"]==1 else 1,row["id"],row["turn"])
    return sorted(base,key=order)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        src,dst=Path(a.validation),Path(a.output)
        if not src.is_file() or src.is_symlink():raise ValueError("invalid input")
        if dst.exists() or dst.is_symlink():raise ValueError("output exists")
        rows=worksheet(json.loads(src.read_text(encoding="utf-8")))
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS)
            w.writeheader();w.writerows(rows)
        print(json.dumps({"rows":len(rows),"unlabeled":sum(not x["final_relevant"] for x in rows),"path":str(dst)},ensure_ascii=False))
    except (OSError,ValueError,json.JSONDecodeError) as e:p.exit(1,f"worksheet failed: {e}\n")
if __name__=="__main__":main()
