"""Calibrated lexical coverage audit: out-of-corpus does not mean invented.

Entire allowed expressions are protected before morphological tokenization.
Audit only; no model edits or runtime blocking.
"""
import argparse,json,re
from pathlib import Path
from build_vocabulary_index_v013588297 import load_jsonl,build

WORD=re.compile(r"[^\W_]",re.UNICODE)

def audit(text,known,tokenizer,allow=()):
    allowed=sorted({x for x in allow if x},key=len,reverse=True)
    spans=re.split("("+"|".join(re.escape(x) for x in allowed)+")",text) if allowed else [text]
    covered=[];out=[];exempt_count=0
    for span in spans:
        if span in allowed:
            exempt_count+=1
            continue
        for m in tokenizer.tokenize(span):
            surface=m.surface()
            if not WORD.search(surface):continue
            covered.append(surface)
            if surface not in known:out.append(surface)
    return {"status":"OUT_OF_CORPUS_REVIEW" if out else "CORPUS_COVERED",
            "corpus_coverage_only":True,"invented_word_confirmed":False,
            "lexical_token_count":len(covered),"exempt_expression_occurrences":exempt_count,
            "out_of_corpus_count":len(out),"out_of_corpus_terms":out,
            "semantic_relevance_evaluated":False,"model_changed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--vocab",default="results/real_persona_vocab_v013588297.json")
    p.add_argument("--text",required=True)
    p.add_argument("--allow",action="append",default=[])
    p.add_argument("--report")
    a=p.parse_args()
    from sudachipy import dictionary
    known=json.loads(Path(a.vocab).read_text(encoding="utf-8-sig"))["counts"]
    report=audit(a.text,known,dictionary.Dictionary().tokenizer(),a.allow)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if a.report:
        path=Path(a.report);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
