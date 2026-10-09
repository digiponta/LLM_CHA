"""v0.2.32.7: independent-ish free generation transfer experiment.

No automatic promotion: held-out probes are limited and manual ratings are
required. Baseline vs candidate tested with both short and legacy prompts.
"""
import argparse,json,hashlib,datetime
from pathlib import Path
from dialogue_guided_generation_v02322 import CheckpointGenerator
from staged_semantic_internalization_v02325 import read_memory
from semantic_backend_worker_v02326 import make_pair

# Authored separately from the 2 approved training utterances.
PROBES=[
 {"kind":"unseen","purpose":"learning","topic":"LLM","user":"言語モデルを基礎から理解するには何を学べばよいですか？","expected":["学習","基礎","モデル"]},
 {"kind":"unseen","purpose":"learning","topic":"LLM","user":"大規模言語モデルの勉強を始める手順を教えて","expected":["学習","基本","言語"]},
 {"kind":"unseen","purpose":"learning,development","topic":"LLM","user":"LLMを学んだ後で自分のモデルを実装する手順は？","expected":["実装","開発","学習"]},
 {"kind":"unseen","purpose":"learning,development","topic":"LLM","user":"言語モデルを理解してから試作品を作る計画を考えて","expected":["試作","構造","学習"]},
 {"kind":"control","purpose":"development","topic":"Python","user":"Pythonでアプリを開発したい","expected":["Python","開発","試作"]},
 {"kind":"control","purpose":"troubleshooting","topic":"GPU","user":"GPUのエラーの原因を調べたい","expected":["GPU","エラー","確認"]},
 {"kind":"control","purpose":"casual","topic":"CPU","user":"CPUについて雑談しよう","expected":["CPU","話"]},
]
LEGACY=[
 {"kind":"legacy","user":"こんにちは","expected":["こんにちは"]},
 {"kind":"legacy","user":"ありがとう","expected":["どういたしまして"]},
 {"kind":"legacy","user":"あなたは誰ですか","expected":["長門有希"]},
 {"kind":"legacy","user":"今日はどんな気分？","expected":[]},
 {"kind":"legacy","user":"最近読んだ本の話をしよう","expected":[]},
 {"kind":"legacy","user":"少し疲れました","expected":[]},
]
PURPOSE={"learning":"学習","development":"開発","troubleshooting":"問題解決","casual":"雑談"}
def prompt_for(p):
    if p["kind"]=="legacy":return f"人: {p['user']}\nAI: "
    purpose=" → ".join(PURPOSE.get(v,v) for v in p["purpose"].split(","))
    return f"話題: {p['topic']}\n目的: {purpose}\n人: {p['user']}\nAI: "

def probes_for(memory):
    records=[r for r in read_memory(memory).values() if r["lifecycle"]=="VALIDATING"]
    if not records:raise ValueError("No candidate records awaiting validation")
    ckpts={r["checkpoint"] for r in records}
    if len(ckpts)!=1:raise ValueError("Multiple candidate checkpoints; assess jobs separately")
    taught=[{"kind":"teacher","id":r["id"],"user":r["context"]["user_input"],
             "topic":r["context"]["topic"],
             "purpose":",".join(r["context"]["purposes"]),
             "expected_answer":r["approved_answer"]} for r in records]
    all_probes=taught+PROBES+LEGACY
    prompts=[prompt_for(x) for x in all_probes]
    if len(prompts)!=len(set(prompts)):raise ValueError("Duplicate evaluation prompts")
    if any(p["user"] in {r["context"]["user_input"] for r in records} for p in PROBES):
        raise ValueError("Probe overlaps teacher utterance")
    return list(ckpts)[0],all_probes

def evaluate(base,candidate,probes,max_new_tokens=80):
    outputs=[]
    for case in probes:
        prompt=prompt_for(case)
        outcomes={}
        for name,model in (("base",base),("candidate",candidate)):
            data=model.generate(prompt,max_new_tokens=max_new_tokens,temperature=0)
            outcomes[name]={k:data[k] for k in ("text","generated_tokens","elapsed_seconds")}
        outputs.append({**case,"prompt":prompt,"outputs":outcomes,
            "manual_review":{"base":{"purpose_fidelity":None,"fluency":None,"factuality":None},
                             "candidate":{"purpose_fidelity":None,"fluency":None,"factuality":None}}})
    return outputs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--memory",default="data/dss_semantic_memory_v02325.jsonl")
    ap.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    ap.add_argument("--candidate",default=None)
    ap.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    ap.add_argument("--max-new-tokens",type=int,default=80)
    ap.add_argument("--out",default="results/semantic_transfer_eval_v02327.json")
    args=ap.parse_args()
    checkpoint,probes=probes_for(args.memory)
    candidate_path=args.candidate or checkpoint
    if Path(candidate_path).resolve()!=Path(checkpoint).resolve():
        raise ValueError("Candidate does not match checkpoint associated with VALIDATING memory")
    base=CheckpointGenerator(args.base,args.tokenizer,args.device)
    candidate=CheckpointGenerator(candidate_path,args.tokenizer,args.device)
    outputs=evaluate(base,candidate,probes,args.max_new_tokens)
    report={"experiment":"v0.2.32.7","executed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "base":args.base,"candidate":candidate_path,
            "results":outputs,"promotion_eligible":False,
            "reason":"Manual independent response-quality ratings and a broader retention suite are required."}
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for r in outputs:
        print(f"[{r['kind']}] {r['user']}")
        print(" base     :",repr(r["outputs"]["base"]["text"]))
        print(" candidate:",repr(r["outputs"]["candidate"]["text"]))
    print("Saved:",dest)
    print("Promotion: BLOCKED pending manual free-generation, generalization, purpose-fidelity and retention evidence.")
if __name__=="__main__":main()
