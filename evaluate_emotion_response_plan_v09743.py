"""Compare frozen Combined-SFT generation with guarded Semantic response plans."""
import argparse,json
from pathlib import Path
from emotion_response_plan_v09743 import plan
from train_emotion_factorial_v09738 import prompt
from evaluate_emotion_generation_v09736 import load
from chat import generate_reply
from contrast_priority_emotion_v09742 import detect_priority

CASES=[
"嬉しいけれど悲しい","悲しいけれど嬉しい",
"楽しかったけど疲れた","悲しくない。むしろ嬉しい。",
"嬉しいけれど悲しいけれど嬉しい",
"悲しくないし、不安ではない","悲しくない",
"悲しいけれど、どうすればいい？","今日は楽しかった",
]
def evaluate(cases,model,tok,runner=generate_reply):
    rows=[]
    for utterance in cases:
        s=detect_priority(utterance)
        p=plan(utterance)
        # Existing Combined-SFT checkpoint uses its original trained labels,
        # NOT the newly invented response-plan strategy tags.
        emotion=s.primary_emotion if s and s.primary_emotion else (s.state if s else "UNKNOWN")
        strategy="ACKNOWLEDGE_MIXED" if s and s.relation=="CONTRAST" else ("ACKNOWLEDGE_NEGATION" if s and s.state=="NEGATED" else "ACKNOWLEDGE_EXPLICIT")
        generated=runner(model,tok,prompt(utterance,emotion,strategy,"both"),
            max_new_tokens=48,temperature=0.0,top_k=3,
            repetition_penalty=1.08,seed=42)
        rows.append({"input":utterance,"state":s.snapshot() if s else None,
                     "plan":p.snapshot() if p else None,
                     "combined_sft_generated":generated.text,
                     "suggested_safe_response":p.response if p else None,
                     "note":"Different formatting/labels can be out of distribution; qualitative only."})
    return {"status":"DIAGNOSTIC_ONLY","count":len(rows),"rows":rows,
            "train_ready":False,"auto_promote":False,
            "limitations":"This is not a controlled generalization score. Existing Combined SFT did not train on v0.9.7.43 plan labels."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",required=True)
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/emotion_response_plan_v09743.json")
    p.add_argument("--cpu",action="store_true")
    a=p.parse_args()
    path=Path(a.output)
    if path.exists():raise FileExistsError(str(path))
    import torch
    device=torch.device("cpu" if a.cpu or not torch.cuda.is_available() else "cuda")
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(a.tokenizer)
    model=load(a.checkpoint,device,tok)
    report=evaluate(CASES,model,tok)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
