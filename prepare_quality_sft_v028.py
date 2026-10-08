"""v0.2.8: filter bland dialogue targets without leaking evaluation data.

Train-only transformations; validation/test files remain byte-for-byte unchanged.
"""
from __future__ import annotations
import argparse, json, random
from pathlib import Path

GENERIC={"そうですね","そう","はい","うん","なるほど","いいですね","わかりました","了解です","そうですか","こんにちは","ありがとう"}
def generic(s):
    normalized=s.strip().rstrip("。.!！?？ ")
    return normalized in GENERIC
def valid(row, min_answer_chars=12):
    q,a=row.get("user"),row.get("assistant")
    if not isinstance(q,str) or not isinstance(a,str):return False
    if not q.strip().startswith("人: ") or not q.strip() or not a.strip():return False
    if generic(a) or len(a.strip())<min_answer_chars:return False
    if len(a)>250 or "＊＊" in a:return False
    return True

def transform(train:Path, anchors:Path, output:Path, *, max_train=25000, seed=42, min_answer_chars=12):
    if max_train<1 or min_answer_chars<1:raise ValueError("positive limits required")
    rng=random.Random(seed)
    data=[json.loads(s) for s in train.read_text(encoding="utf-8").splitlines() if s.strip()]
    before=len(data)
    data=[r for r in data if valid(r,min_answer_chars)]
    if not data:raise ValueError("No rows survived quality filtering")
    rng.shuffle(data)
    data=data[:max_train]
    anchor_rows=[json.loads(s) for s in anchors.read_text(encoding="utf-8").splitlines() if s.strip()]
    for row in anchor_rows:
        if not isinstance(row.get("user"),str) or not isinstance(row.get("assistant"),str):raise ValueError("Malformed anchor")
        row["user"]="人: "+row["user"].strip()
    output.mkdir(parents=True,exist_ok=True)
    def write(name, rows):
        with (output/name).open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    write("quality_train.jsonl",data)
    write("persona_anchors_preformatted.jsonl",anchor_rows)
    stats={"input_rows":before,"eligible_rows":sum(valid(r,min_answer_chars) for r in
           [json.loads(s) for s in train.read_text(encoding="utf-8").splitlines() if s.strip()]),
           "selected_rows":len(data),"anchor_rows":len(anchor_rows),"seed":seed,
           "note":"Validation/test untouched. Longer answers not guaranteed better."}
    (output/"manifest.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return stats

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",type=Path,default=Path("data/realpersonachat_multiturn/rpc_multiturn_train.jsonl"))
    p.add_argument("--anchors",type=Path,default=Path("data/realpersonachat_replay/rpc_replay_anchors.jsonl"))
    p.add_argument("--output",type=Path,default=Path("data/realpersonachat_quality"))
    p.add_argument("--max-train",type=int,default=25000)
    p.add_argument("--min-answer-chars",type=int,default=12)
    a=p.parse_args()
    print(json.dumps(transform(a.train,a.anchors,a.output,max_train=a.max_train,min_answer_chars=a.min_answer_chars),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
