"""v0.2.32.4 held-out checkpoint comparison; does not train on test topics."""
import argparse,json
from pathlib import Path
from dialogue_guided_generation_v02322 import CheckpointGenerator,prompt_raw
from prepare_purpose_sft_v02324 import build,REPLAY

def run(base,trained,rows,max_new_tokens=64):
    result=[]
    for row in rows:
        item={"id":row.get("id","replay"),"purpose":row.get("purpose"),
              "topic":row.get("topic"),"user":row.get("user"),
              "target":row["answer"],"prompt":row["prompt"],"outputs":{}}
        for key,g in [("base",base),("sft",trained)]:
            item["outputs"][key]=g.generate(row["prompt"],max_new_tokens=max_new_tokens,temperature=0)
        result.append(item)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--trained",default="model/model-llm-cha-purpose-sft-v02324.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=["auto","cpu","cuda"],default="auto")
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--out",default="results/purpose_sft_heldout_v02324.json")
    a=p.parse_args()
    base=CheckpointGenerator(a.base,a.tokenizer,a.device)
    trained=CheckpointGenerator(a.trained,a.tokenizer,a.device)
    test=build()["test"]
    rows=run(base,trained,test,a.max_new_tokens)
    # Separate old-format probes to inspect catastrophic forgetting.
    replay=[dict(id="legacy-replay-"+str(i),purpose="legacy",topic="legacy",
                 user="",prompt=r["prompt"],answer=r["answer"]) for i,r in enumerate(REPLAY)]
    retention=run(base,trained,replay,a.max_new_tokens)
    report={"heldout_test":rows,"legacy_replay":retention,
            "important":"Human evaluation required; heldout shares response templates and is not an independent final benchmark."}
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for group,items in [("TEST",rows),("REPLAY",retention)]:
        for item in items:
            print(f'[{group}] {item["id"]} / target={item["target"]}')
            print(" base:",repr(item["outputs"]["base"]["text"]))
            print("  sft:",repr(item["outputs"]["sft"]["text"]))
    print("Saved:",path)
    print("Review semantic correctness, purpose fidelity, fluency and regression manually.")
if __name__=="__main__":main()
