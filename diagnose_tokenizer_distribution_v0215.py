"""v0.2.15: tokenizer fragmentation and generic-response distribution audit.

Observational diagnosis only; does not modify model weights or training files.
"""
from __future__ import annotations
import argparse,collections,json,statistics
from pathlib import Path
from tokenizer_bpe import Tokenizer
from conversation_diagnostics_v026 import classify_quality,GENERIC

def norm(s):
    return s.strip().rstrip("。!?！？ ")
def analyze(rows,tok):
    answers=[r["assistant"] for r in rows if isinstance(r.get("assistant"),str) and isinstance(r.get("user"),str)]
    if not answers:raise ValueError("No valid Q/A rows")
    freq=collections.Counter(norm(a) for a in answers)
    token_counts=[len(tok.encode(a)) for a in answers]
    unk=sum(sum(t==tok.unk_id for t in tok.encode(a)) for a in answers)
    tokens=sum(token_counts)
    chars=sum(len(a) for a in answers)
    generic=sum(classify_quality(r["user"].rsplit("人: ",1)[-1],r["assistant"])["generic"] for r in rows if isinstance(r.get("assistant"),str) and isinstance(r.get("user"),str))
    return {"rows":len(answers),"generic_fraction":round(generic/len(answers),5),
            "top_responses":[{"text":k,"count":v,"fraction":round(v/len(answers),5)} for k,v in freq.most_common(15)],
            "unique_fraction":round(len(freq)/len(answers),5),
            "tokens_per_character":round(tokens/max(chars,1),5),
            "chars_per_token":round(chars/max(tokens,1),5),
            "median_tokens_per_answer":statistics.median(token_counts),
            "unknown_token_fraction":round(unk/max(tokens,1),7),
            "short_under_8_chars_fraction":round(sum(len(norm(a))<8 for a in answers)/len(answers),5),
            "generic_dictionary":sorted(GENERIC)}
def read_rows(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(x) for x in handle if x.strip()]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--datasets",nargs="+",default=[
        "data/realpersonachat_quality/quality_train.jsonl",
        "data/dialogue_sft_v0211/dialogue_train.jsonl",
        "data/dialogue_generalization_v0212/train.jsonl",
        "data/dialogue_generalization_v0212/test.jsonl"])
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--max-rows",type=int,default=50000)
    p.add_argument("--output",default="results/tokenizer_distribution_v0215.json")
    a=p.parse_args()
    tok=Tokenizer.load(a.tokenizer)
    report={"tokenizer":a.tokenizer,"datasets":{}}
    for source in a.datasets:
        path=Path(source)
        if not path.is_file():
            report["datasets"][source]={"error":"missing file"};continue
        report["datasets"][source]=analyze(read_rows(path)[:a.max_rows],tok)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
