"""Build an auditable lexical vocabulary from authorized local Japanese conversations.

Requires sudachipy + sudachidict_core. No model training or checkpoint changes.
"""
import argparse,collections,json,re
from pathlib import Path

def tokenize(text,tokenizer):
    return [m.surface() for m in tokenizer.tokenize(text) if m.surface().strip()]

def build(records, tokenizer, min_count=2):
    counts=collections.Counter()
    for row in records:
        for key in ("user","assistant"):
            value=row.get(key,"")
            if not isinstance(value,str):raise ValueError("Invalid text: "+key)
            counts.update(tokenize(value,tokenizer))
    # Do not count punctuation as evidence for actual known words
    kept={w:c for w,c in counts.items() if c>=min_count and re.search(r"[^\W_]",w,re.UNICODE)}
    return {"format":"llm-cha-vocab-v1","min_count":min_count,
            "observed_types":len(counts),"allowed_types":len(kept),
            "counts":dict(sorted(kept.items())),"source":"real-persona-cp-pilot"}
def load_jsonl(path):
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        if line.strip():yield json.loads(line)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/real_persona_pilot_v013588293.jsonl")
    p.add_argument("--output",default="results/real_persona_vocab_v013588297.json")
    p.add_argument("--min-count",type=int,default=2)
    a=p.parse_args()
    if a.min_count<1:raise ValueError("min-count must be positive")
    try:
        from sudachipy import dictionary
    except ImportError as e:
        raise SystemExit("Install: python -m pip install sudachipy sudachidict_core") from e
    result=build(load_jsonl(a.input),dictionary.Dictionary().create(),a.min_count)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="counts"},ensure_ascii=False))
if __name__=="__main__":main()
