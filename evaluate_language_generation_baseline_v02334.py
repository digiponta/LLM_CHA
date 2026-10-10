"""v0.2.33.4: no-DSS/no-Bridge language generation capability baseline.

Evaluates the actual frozen LLM before further semantic interventions.
No model training, semantic inputs, automatic grading, or promotion.
"""
import argparse,json,datetime,hashlib
from pathlib import Path
from dialogue_guided_generation_v02322 import CheckpointGenerator

# Pre-authored diagnostics; these are exploratory, NOT a sealed benchmark.
TASKS=[
 {"id":"A1","ability":"continuation","prompt":"人: 次の文章を自然に続けてください。\nAI: 今日は天気がよいので、","expectation":"自然な日本語で文を完結する"},
 {"id":"A2","ability":"continuation","prompt":"人: この文章の続きを書いてください。\nAI: パソコンの電源を入れた後、","expectation":"自然な続きを生成する"},
 {"id":"B1","ability":"explanation","prompt":"人: CPUとは何ですか？\nAI: ","expectation":"CPUを正しく定義する"},
 {"id":"B2","ability":"explanation","prompt":"人: Pythonとは何ですか？\nAI: ","expectation":"Pythonを正しく説明する"},
 {"id":"C1","ability":"procedure","prompt":"人: 簡単なプログラムを作る手順を、まず・次に・最後にの順で説明してください。\nAI: ","expectation":"順序のある実行可能な手順"},
 {"id":"C2","ability":"procedure","prompt":"人: お茶を入れる手順を順番に説明してください。\nAI: ","expectation":"一般的に妥当な順序の手順"},
 {"id":"D1","ability":"context","prompt":"人: 私はPythonを勉強しています。\nAI: そうですね。\n人: その言語を使うには何から始めればよいですか？\nAI: ","expectation":"『その言語』をPythonとして扱う"},
 {"id":"D2","ability":"context","prompt":"人: GPUの仕組みについて知りたい。\nAI: 分かりました。\n人: それはCPUとどう違いますか？\nAI: ","expectation":"『それ』をGPUとして扱いCPUと比較する"},
 {"id":"E1","ability":"conditioning","prompt":"人: CPUについて、初心者向けに短く説明してください。\nAI: ","expectation":"CPUを初心者向けに簡潔に説明する"},
 {"id":"E2","ability":"conditioning","prompt":"人: Pythonを学んでから小さなアプリを作るための計画を教えてください。\nAI: ","expectation":"学習→開発の順序に沿った計画を提示する"},
 {"id":"R1","ability":"retention","prompt":"人: こんにちは\nAI: ","expectation":"挨拶できる"},
 {"id":"R2","ability":"retention","prompt":"人: ありがとう\nAI: ","expectation":"感謝に自然に応答する"},
 {"id":"R3","ability":"retention","prompt":"人: あなたは誰ですか\nAI: ","expectation":"既存の自己紹介傾向を記録する"}
]
ABILITY={"continuation":"A","explanation":"B","procedure":"C","context":"D","conditioning":"E","retention":"R"}

def verify_tasks(tasks=TASKS):
    ids=[r["id"] for r in tasks]
    prompts=[r["prompt"] for r in tasks]
    if len(ids)!=len(set(ids)) or len(prompts)!=len(set(prompts)):
        raise ValueError("Duplicate evaluation IDs/prompts")
    for r in tasks:
        if not r["prompt"].endswith("AI: ") or ABILITY.get(r["ability"])!=r["id"][0]:
            raise ValueError("Bad task: "+r["id"])
    return True

def evaluate(generators,tasks=TASKS,max_new_tokens=80):
    verify_tasks(tasks)
    result=[]
    for r in tasks:
        answers={name:gen.generate(r["prompt"],max_new_tokens=max_new_tokens,temperature=0)
                 for name,gen in generators.items()}
        result.append({**r,"outputs":answers,
          "manual_review":{name:{"fluency":None,"task_success":None,
                      "factuality":None,"notes":""} for name in generators}})
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    ap.add_argument("--compare",default=None,help="Optional second checkpoint; no change to base")
    ap.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    ap.add_argument("--max-new-tokens",type=int,default=80)
    ap.add_argument("--out",default="results/language_generation_baseline_v02334.json")
    a=ap.parse_args()
    if a.max_new_tokens<1:raise ValueError("max-new-tokens must be positive")
    gens={"base":CheckpointGenerator(a.base,a.tokenizer,a.device)}
    if a.compare:gens["comparison"]=CheckpointGenerator(a.compare,a.tokenizer,a.device)
    results=evaluate(gens,max_new_tokens=a.max_new_tokens)
    report={"experiment":"v0.2.33.4","generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "checkpoints":{"base":a.base,**({"comparison":a.compare} if a.compare else {})},
            "DSS_used":False,"semantic_memory_used":False,"bridge_used":False,
            "status":"EXPLORATORY_MANUAL_REVIEW_REQUIRED","promotion_eligible":False,
            "limitations":["Small authored exploratory probe set, not sealed independent benchmark",
                "Greedy outputs alone do not isolate knowledge from prompt-format mismatch",
                "No automated quality score or semantic internalization determination"],"results":results}
    out=Path(a.out)
    if out.exists():raise FileExistsError(f"Refuse to overwrite report: {out}")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for r in results:
        print(f"[{r['id']} {r['ability']}] {r['expectation']}")
        for name,val in r["outputs"].items():print("  ",name,repr(val["text"]))
    print("Saved",out)
if __name__=="__main__":main()
