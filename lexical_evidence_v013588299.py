"""Lexical evidence diagnostic; unknown compositions are candidates for review, not proven coinages."""
import argparse,json,re
from pathlib import Path

def classify(text, tokenizer, corpus_counts, specialized=()):
    protected=sorted(set(filter(None,specialized)),key=len,reverse=True)
    fragments=re.split("("+"|".join(map(re.escape,protected))+")",text) if protected else [text]
    items=[]
    for fragment in fragments:
        if fragment in protected:
            items.append({"surface":fragment,"category":"SPECIALIZED_TERM","is_oov":None,"corpus_count":None})
            continue
        for morpheme in tokenizer.tokenize(fragment):
            surface=morpheme.surface()
            if not re.search(r"[^\W_]",surface,re.UNICODE):continue
            count=corpus_counts.get(surface,0)
            oov=morpheme.is_oov()
            category="KNOWN_WORD" if not oov else "CORPUS_ONLY" if count else "UNKNOWN_COMPOSITION"
            items.append({"surface":surface,"category":category,"is_oov":oov,"corpus_count":count})
    return {"status":"REVIEW_REQUIRED" if any(i["category"]=="UNKNOWN_COMPOSITION" for i in items) else "LEXICALLY_SUPPORTED",
            "items":items,"counts":{k:sum(i["category"]==k for i in items) for k in ("KNOWN_WORD","CORPUS_ONLY","SPECIALIZED_TERM","UNKNOWN_COMPOSITION")},
            "meaning_verified":False,"compound_usage_verified":False,"generation_blocked":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vocab",default="results/real_persona_vocab_v013588297.json")
    ap.add_argument("--text",required=True)
    ap.add_argument("--allow",action="append",default=[])
    ap.add_argument("--output")
    a=ap.parse_args()
    from sudachipy import dictionary
    counts=json.loads(Path(a.vocab).read_text(encoding="utf-8-sig"))["counts"]
    result=classify(a.text,dictionary.Dictionary().tokenizer(),counts,a.allow)
    if a.output:
        dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
