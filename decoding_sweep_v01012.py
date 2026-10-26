"""v0.10.1.2 length × beam sweep, frozen checkpoint, reference-blind decoding."""
import argparse, csv, hashlib, importlib, json, statistics, time
from pathlib import Path
from semantic_decode_v0101 import decode

def sweep(model, tokenizer, cases, lengths=(16,32,48,64,96), widths=(1,3,5)):
    rows=[]
    for case in cases:
        prompt, ref = case["prompt"], case["reference"]
        reference_ids=tokenizer.encode(ref,add_bos=False)
        for cap in lengths:
            for width in widths:
                output=decode(model,tokenizer,prompt,beam_width=width,max_new_tokens=cap,
                              repetition_penalty=1.,length_penalty=1.)
                prefix=0
                for a,b in zip(output.token_ids, reference_ids):
                    if a!=b: break
                    prefix+=1
                rows.append({
                    "id":case["id"],"split":case.get("split","dev"),"method":f"beam{width}" if width>1 else "greedy",
                    "beam_width":width,"max_new_tokens":cap,"exact_match":output.text.strip()==ref.strip(),
                    "matched_prefix_tokens":prefix,"reference_tokens":len(reference_ids),
                    "generated_tokens":len(output.token_ids),"hit_token_cap":len(output.token_ids)>=cap,
                    "latency_ms":round(output.elapsed_ms,3),"output":output.text,
                    "reference":ref
                })
    return rows

def summarize(rows):
    result=[]
    groups=sorted(set((r["beam_width"],r["max_new_tokens"]) for r in rows))
    for width,cap in groups:
        data=[r for r in rows if (r["beam_width"],r["max_new_tokens"])==(width,cap)]
        result.append({"decoder":"greedy" if width==1 else f"beam{width}",
                       "max_tokens":cap,"n":len(data),
                       "exact":sum(r["exact_match"] for r in data),
                       "exact_rate":round(sum(r["exact_match"] for r in data)/len(data),6),
                       "mean_prefix":round(statistics.mean(r["matched_prefix_tokens"] for r in data),3),
                       "cap_hit_count":sum(r["hit_token_cap"] for r in data),
                       "mean_latency_ms":round(statistics.mean(r["latency_ms"] for r in data),3)})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cases",default="data/decoding_dev_v0101.json")
    p.add_argument("--factory",default="decoder_factory_v0101:load")
    p.add_argument("--output",default="results/decoding_sweep_v01012.json")
    p.add_argument("--lengths",default="16,32,48,64,96")
    p.add_argument("--widths",default="1,3,5")
    a=p.parse_args()
    cases=json.loads(Path(a.cases).read_text(encoding="utf-8-sig"))
    if not isinstance(cases,list) or not cases or any(not all(k in c for k in ("id","prompt","reference")) for c in cases):
        raise ValueError("Expected nonempty cases array with id, prompt, reference")
    lengths=tuple(int(v) for v in a.lengths.split(","))
    widths=tuple(int(v) for v in a.widths.split(","))
    if not lengths or not widths or min(lengths)<1 or min(widths)<1: raise ValueError("Invalid sweep parameters")
    module,fun=a.factory.split(":",1)
    model,tok=getattr(importlib.import_module(module),fun)()
    rows=sweep(model,tok,cases,lengths,widths)
    summary=summarize(rows)
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    payload={"protocol":"TRAIN_ASSOCIATED_DEV_NOT_HOLDOUT","cases":len(cases),
             "sha256_cases":hashlib.sha256(Path(a.cases).read_bytes()).hexdigest(),
             "lengths":lengths,"widths":widths,"summary":summary,"records":rows}
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    with target.with_suffix(".csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",target)

if __name__=="__main__":main()
