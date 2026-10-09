"""Convert grounded single-turn examples into existing preformatted trainer schema."""
import argparse,json
from pathlib import Path

def convert(rows):
    out=[]
    for row in rows:
        user,answer=row["user"],row["assistant"]
        if user.startswith("人: ") or "\nAI: " in user:raise ValueError("unexpected preformatted input")
        if not user.strip() or not answer.strip():raise ValueError("empty field")
        out.append({"user":"人: "+user,"assistant":answer})
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data/topic_grounded_v02290/train.jsonl")
    p.add_argument("--output",default="data/topic_grounded_v02290/train_preformatted.jsonl")
    a=p.parse_args()
    source=Path(a.source)
    if not source.exists():p.error("run prepare_topic_grounded_v02290.py first")
    original=[json.loads(s) for s in source.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    rows=convert(original)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    print("Topic-grounded train rows:",len(rows),"saved:",dest)
if __name__=="__main__":main()
