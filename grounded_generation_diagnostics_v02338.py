"""v0.2.33.8 Grounded Generation Diagnostics; evaluation only.

Tests copying, extraction, transformation, gold-prefix completion,
and counterfactual grounding without modifying DSS or any checkpoint.
"""
import argparse,datetime,json
from pathlib import Path
from dialogue_guided_generation_v02322 import CheckpointGenerator

FACTS=[
 ("ブラウザ","Webページを表示するソフトウェア"),
 ("電池","化学エネルギーを電気エネルギーに変換する装置"),
 ("マイク","音を電気信号に変換する装置"),
]
CASES=[
 {"id":"A1","axis":"copy","prompt":"人: 次の文章をそのまま出力してください。\n文章: ブラウザはWebページを表示するソフトウェアです。\nAI: ","target":"ブラウザはWebページを表示するソフトウェアです。"},
 {"id":"A2","axis":"copy","prompt":"人: 次の文章をそのまま出力してください。\n文章: 電池は化学エネルギーを電気エネルギーに変換する装置です。\nAI: ","target":"電池は化学エネルギーを電気エネルギーに変換する装置です。"},
 {"id":"B1","axis":"extract","prompt":"人: 次の情報からブラウザの役割だけ答えてください。\n情報: CPUは命令を実行します。ブラウザはWebページを表示します。電池は電力を供給します。\nAI: ","target":"ブラウザはWebページを表示します。"},
 {"id":"B2","axis":"extract","prompt":"人: 次の情報から電池の役割だけ答えてください。\n情報: マイクは音を検出します。電池は電力を供給します。GPUは並列計算を行います。\nAI: ","target":"電池は電力を供給します。"},
 {"id":"C1","axis":"transform","prompt":"人: 次の内容を一文の定義にしてください。\n内容: センサー / 温度を検出する装置\nAI: ","target":"センサーは温度を検出する装置です。"},
 {"id":"C2","axis":"transform","prompt":"人: 次の内容を順序のある手順文にしてください。\n内容: 1.道具を用意する 2.機器を調べる 3.結果を記録する\nAI: ","target":"まず道具を用意する。次に機器を調べる。最後に結果を記録する。"},
 {"id":"D1","axis":"completion","prompt":"人: ブラウザの役割を説明してください。\nAI: ブラウザはWebページを","target":"表示するソフトウェアです。","prefix":"ブラウザはWebページを"},
 {"id":"D2","axis":"completion","prompt":"人: 機器を点検する手順を説明してください。\nAI: まず道具を用意し、次に","target":"機器を調べ、最後に結果を記録します。","prefix":"まず道具を用意し、次に"},
 {"id":"E1","axis":"counterfactual","prompt":"人: 次の与えられた設定に従って答えてください。これは架空の定義です。\n設定: 架空装置アルファは赤い光を出す装置です。\nAI: ","target":"架空装置アルファは赤い光を出す装置です。","fact":"赤い光"},
 {"id":"E2","axis":"counterfactual","prompt":"人: 次の与えられた設定に従って答えてください。これは架空の定義です。\n設定: 架空装置アルファは青い光を出す装置です。\nAI: ","target":"架空装置アルファは青い光を出す装置です。","fact":"青い光"},
]
def validate_cases(cases=CASES):
    ids=[c["id"] for c in cases]
    if len(ids)!=len(set(ids)) or len({c["prompt"] for c in cases})!=len(cases):
        raise ValueError("Duplicate IDs or prompts")
    allowed={"copy":"A","extract":"B","transform":"C","completion":"D","counterfactual":"E"}
    for c in cases:
        if c["axis"] not in allowed or c["id"][0]!=allowed[c["axis"]] or "\nAI: " not in c["prompt"]:
            raise ValueError("Invalid case: "+c["id"])
    return True

def run(generators,cases=CASES,max_new_tokens=80):
    validate_cases(cases)
    results=[]
    for c in cases:
        outputs={}
        for name,g in generators.items():
            d=g.generate(c["prompt"],max_new_tokens=max_new_tokens,temperature=0)
            # String equality is a diagnostic only; for non-copy tasks,
            # multiple correct phrasings can exist.
            outputs[name]={**d,"exact_target":d["text"]==c["target"],
                           "manual_review":{"fidelity":None,"fluency":None,"notes":""}}
        results.append({**c,"outputs":outputs})
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--candidate",default="model/model-llm-cha-content-structure-v02337.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--out",default="results/grounded_generation_diagnostics_v02338.json")
    a=p.parse_args()
    if a.max_new_tokens<1:raise ValueError("max-new-tokens must be positive")
    if Path(a.out).exists():raise FileExistsError(f"Refusing overwrite: {a.out}")
    gens={"base":CheckpointGenerator(a.base,a.tokenizer,a.device),
          "candidate":CheckpointGenerator(a.candidate,a.tokenizer,a.device)}
    results=run(gens,max_new_tokens=a.max_new_tokens)
    report={"experiment":"v0.2.33.8","evaluated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "models":{"base":a.base,"candidate":a.candidate},"results":results,
            "training_performed":False,"dss_used":False,"semantic_memory_used":False,
            "bridge_used":False,"promotion_eligible":False,
            "limitations":["Small authored diagnostic; exact match is not semantic correctness",
                "Completion probes supply the gold response prefix; result does not prove free generation",
                "Counterfactual variants test prompt influence, not truthfulness or learned semantic knowledge",
                "Manual ratings and independent held-out benchmarks required"]}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for r in results:
        print(f"[{r['id']} {r['axis']}] target={r['target']!r}")
        for name,d in r["outputs"].items():
            print(f" {name}: {d['text']!r} exact={d['exact_target']}")
    print("Saved:",dest)
if __name__=="__main__":main()
