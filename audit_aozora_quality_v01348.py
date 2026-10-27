"""v0.13.48 read-only audit of Japanese literary corpus.
Flags POSSIBLE inline ruby; never automatically strips hiragana.
Preserves text and does not approve training.
"""
import argparse,collections,json,re,statistics,hashlib
from pathlib import Path

# A diagnostic heuristic, NOT a ruby detector: kanji followed by 2-8 kana.
# Common inflections and okurigana can match; manual review required.
INLINE_RE=re.compile(r"([一-龯々〆ヶ]{1,6})([ぁ-ゖ]{2,8})")
def assess(lines,tokenizer=None,max_examples=30):
    lengths=[len(s) for s in lines]
    patterns=collections.Counter()
    samples=[]
    for lineno,line in enumerate(lines,1):
        for m in INLINE_RE.finditer(line):
            token=m.group()
            patterns[token]+=1
            if len(samples)<max_examples:
                samples.append({"line":lineno,"text":token,"context":line[max(0,m.start()-10):m.end()+10]})
    tok_counts=[len(tokenizer.encode(s)) for s in lines] if tokenizer else []
    anomalies=[{"line":i,"chars":len(s),"reason":"LONG_SENTENCE" if len(s)>500 else "REPLACEMENT_CHARACTER"}
               for i,s in enumerate(lines,1) if len(s)>500 or "\ufffd" in s]
    return {"version":"v0.13.48","status":"REVIEW_REQUIRED",
            "sentences":len(lines),"characters":sum(lengths),
            "bpe_tokens":sum(tok_counts) if tok_counts else None,
            "bpe_mean_per_sentence":round(statistics.mean(tok_counts),2) if tok_counts else None,
            "possible_ruby_occurrences":sum(patterns.values()),
            "possible_ruby_unique":len(patterns),
            "possible_ruby_top":[{"text":word,"count":count} for word,count in patterns.most_common(30)],
            "possible_ruby_examples":samples,
            "anomalies":anomalies[:100],
            "training_approved":False,
            "interpretation":"Heuristic detects ordinary okurigana too. Inspect source and examples before making edits.",
            "source_independence_verified":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("results/aozora_789_foundation_v01347.txt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/aozora_789_quality_v01348.json"))
    p.add_argument("--max-examples",type=int,default=30)
    a=p.parse_args()
    if not a.input.is_file():p.error(f"missing input: {a.input}")
    if not a.tokenizer.is_file():p.error(f"missing tokenizer: {a.tokenizer}")
    if a.output.exists():p.error("refusing to overwrite audit")
    if a.max_examples<1:p.error("max examples must be positive")
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(a.tokenizer))
    lines=[s.strip() for s in a.input.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    report=assess(lines,tok,a.max_examples)
    report["sha256"]={"input":hashlib.sha256(a.input.read_bytes()).hexdigest(),
                      "tokenizer":hashlib.sha256(a.tokenizer.read_bytes()).hexdigest()}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","sentences","characters","bpe_tokens",
          "possible_ruby_occurrences","possible_ruby_unique")},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
