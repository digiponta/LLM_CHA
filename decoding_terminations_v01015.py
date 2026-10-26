"""v0.10.1.5 termination reason measurement (reference-blind decoding)."""
import argparse, importlib, json, unicodedata
from collections import Counter
from pathlib import Path
from semantic_decode_v0101 import decode

def run(model, tokenizer, cases, max_new_tokens=48):
    records=[]
    for case in cases:
        for name,width in (("greedy",1),("beam3",3)):
            out=decode(model,tokenizer,case["prompt"],beam_width=width,max_new_tokens=max_new_tokens)
            ref=case["reference"]
            records.append({"id":case["id"],"decoder":name,"termination_reason":out.termination_reason,
                            "generated_tokens":len(out.token_ids),"latency_ms":round(out.elapsed_ms,3),
                            "exact_match":out.text.strip()==ref.strip(),
                            "normalized_exact_match":unicodedata.normalize("NFKC",out.text.strip())==
                                                      unicodedata.normalize("NFKC",ref.strip()),
                            "output":out.text,"reference":ref})
    summary={}
    for name in ("greedy","beam3"):
        rows=[r for r in records if r["decoder"]==name]
        summary[name]={"count":len(rows),"exact":sum(x["exact_match"] for x in rows),
                       "normalized_exact":sum(x["normalized_exact_match"] for x in rows),
                       "termination_counts":dict(Counter(x["termination_reason"] for x in rows))}
    return {"protocol":"TRAIN_ASSOCIATED_DEV_NOT_HOLDOUT",
            "max_new_tokens":max_new_tokens,"summary":summary,"records":records}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cases",default="data/decoding_dev_v0101.json")
    p.add_argument("--factory",default="decoder_factory_v0101:load")
    p.add_argument("--output",default="results/decoding_terminations_v01015.json")
    p.add_argument("--length",type=int,default=48)
    a=p.parse_args()
    cases=json.loads(Path(a.cases).read_text(encoding="utf-8-sig"))
    mod,func=a.factory.split(":",1)
    model,tokenizer=getattr(importlib.import_module(mod),func)()
    result=run(model,tokenizer,cases,a.length)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result["summary"],ensure_ascii=False,indent=2))
    print("report:",dest)
if __name__=="__main__":main()
